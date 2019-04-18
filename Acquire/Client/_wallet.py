
# use a variable so we can monkey-patch while testing
_input = input

__all__ = ["Wallet"]


def _flush_output():
    """Flush STDOUT"""
    try:
        import sys as _sys
        _sys.stdout.flush()
    except:
        pass


def _read_json(filename):
    """Return a json-decoded dictionary from the data written
       to 'filename'
    """
    import json as _json
    with open(filename, "rb") as FILE:
        s = FILE.read().decode("utf-8")
        return _json.loads(s)


def _write_json(data, filename):
    """Write the passed json-encodable dictionary to 'filename'"""
    import json as _json
    s = _json.dumps(data)
    with open(filename, "wb") as FILE:
        FILE.write(s.encode("utf-8"))


def _read_service(filename):
    """Read and return the service written to 'filename'"""
    from Acquire.Client import Service as _Service
    return _Service.from_data(_read_json(filename))


def _write_service(service, filename):
    """Write the passed service to 'filename'"""
    _write_json(service.to_data(), filename)


class Wallet:
    """This class holds a wallet that can be used to simplify
       sending passwords and one-time-password (OTP) codes
       to an acquire identity service.

       This holds a wallet of passwords and (optionally)
       OTP secrets that are encrypted using a local keypair
       that is unlocked by a password supplied by the user locally.

       By default this will create the wallet in your home
       directory ($HOME/.acquire_wallet). If you want the wallet
       to be saved in a different directory, specify that
       as "wallet_dir".
    """
    def __init__(self, wallet_dir=None, wallet_password=None):
        self._wallet_key = None
        self._cache = {}
        self._service_info = {}
        self._manual_password = False
        self._manual_otpcode = False
        self._device_uid = None

        import os as _os

        if wallet_dir is None:
            home = _os.path.expanduser("~")
            wallet_dir = "%s/.acquire_wallet" % home

        if not _os.path.exists(wallet_dir):
            _os.mkdir(wallet_dir)
        elif not _os.path.isdir(wallet_dir):
            raise TypeError("The wallet directory must be a directory!")

        self._wallet_dir = wallet_dir

        if wallet_password is not None:
            self._get_wallet_key(wallet_password=wallet_password)

    def _create_wallet_key(self, filename, wallet_password=None):
        """Create a new wallet key for the user"""

        if wallet_password is not None:
            password = wallet_password
        else:
            import getpass as _getpass
            password = _getpass.getpass(
                     prompt="Please enter a password to encrypt your wallet: ")

        from Acquire.Client import PrivateKey as _PrivateKey
        key = _PrivateKey()

        bytes = key.bytes(password)

        if wallet_password is not None:
            password2 = wallet_password
        else:
            import getpass as _getpass
            password2 = _getpass.getpass(
                            prompt="Please confirm the password: ")

        if password != password2:
            print("The passwords don't match. Please try again.")
            self._create_wallet_key(filename)
            return

        # the passwords match - write this to the file
        with open(filename, "wb") as FILE:
            FILE.write(bytes)

        return key

    def _get_wallet_key(self, wallet_password=None):
        """Return the private key used to encrypt everything in the wallet.
           This will ask for the users password
        """
        if self._wallet_key:
            return self._wallet_key

        wallet_dir = self._wallet_dir

        keyfile = "%s/wallet_key.pem" % wallet_dir

        import os as _os

        if not _os.path.exists(keyfile):
            self._wallet_key = self._create_wallet_key(
                                            filename=keyfile,
                                            wallet_password=wallet_password)
            return self._wallet_key

        # read the keyfile and decrypt
        with open(keyfile, "rb") as FILE:
            bytes = FILE.read()

        wallet_key = None

        from Acquire.Client import PrivateKey as _PrivateKey

        if wallet_password is not None:
            wallet_key = _PrivateKey.read_bytes(bytes, wallet_password)

        # get the user password
        import getpass as _getpass
        while not wallet_key:
            password = _getpass.getpass(
                            prompt="Please enter your wallet password: ")

            try:
                wallet_key = _PrivateKey.read_bytes(bytes, password)
            except:
                print("Invalid password. Please try again.")

        self._wallet_key = wallet_key
        return wallet_key

    def _get_userfile(self, username, identity_url):
        """Return the userfile for the passed username logging into the
           passed identity url"""
        from Acquire.ObjectStore import string_to_safestring \
            as _string_to_safestring
        return "%s/user_%s_%s_encrypted" % (
            self._wallet_dir,
            _string_to_safestring(username),
            _string_to_safestring(identity_url))

    def remove_user_info(self, username):
        """Call this function to remove the userinfo associated
           with the account 'username' for all identity services
        """
        wallet_dir = self._wallet_dir

        import glob as _glob
        import os as _os

        userfiles = _glob.glob("%s/user_*_encrypted" % wallet_dir)

        for userfile in userfiles:
            try:
                userinfo = self._read_userfile(userfile)
                if userinfo["username"] == username:
                    _os.unlink(userfile)
            except:
                pass

    def _read_userfile(self, filename):
        """Read all info from the passed userfile"""
        try:
            return self._cache[filename]
        except:
            pass

        import os as _os

        if not _os.path.exists(filename):
            return

        data = _read_json(filename)

        from Acquire.ObjectStore import string_to_bytes \
            as _string_to_bytes

        try:
            data["password"] = _string_to_bytes(data["password"])
        except:
            pass

        try:
            data["otpsecret"] = _string_to_bytes(data["otpsecret"])
        except:
            pass

        self._cache[filename] = data
        return data

    def _read_userinfo(self, username, identity_url):
        """Read all info for the passed user at the identity service
           reached at 'identity_url'"""
        return self._read_userfile(self._get_userfile(username,
                                                      identity_url))

    def _get_username(self):
        """Function to find a username automatically, of if that fails,
           to ask the user
        """
        wallet_dir = self._wallet_dir

        import glob as _glob

        userfiles = _glob.glob("%s/user_*_encrypted" % wallet_dir)

        userinfos = {}

        from Acquire.ObjectStore import safestring_to_string \
            as _safestring_to_string

        for userfile in userfiles:
            try:
                userinfo = self._read_userfile(userfile)
                username = _safestring_to_string(userinfo["username"])
                userinfos[username] = userinfo
            except:
                pass

        usernames = list(userinfos.keys())
        usernames.sort()

        if len(usernames) == 1:
            return usernames[0]

        if len(usernames) == 0:
            return _input("Please type your username: ")

        print("Please choose the account by typing in its number, "
              "or type a new username if you want a different account.")

        for (i, username) in enumerate(usernames):
            print("[%d] %s" % (i+1, username))

        username = None

        while not username:
            print("Make your selection: ", end="")

            reply = _input(
                    "Make your selection (1 to %d) " %
                    (len(usernames))
                )

            try:
                idx = int(reply) - 1

                if idx < 0 or idx >= len(usernames):
                    print("Invalid account. Try again...")
                else:
                    username = usernames[idx]
            except:
                username = None

        return username

    def _get_user_password(self, username, identity_url):
        """Get the user password for the passed user on the passed
           identity_url. If remember_device then save the
           password in the wallet if it is not already there
        """
        try:
            userinfo = self._read_userinfo(username, identity_url)

            if userinfo:
                password = userinfo["password"]
                self._manual_password = False

                # this needs to be decrypted
                return self._get_wallet_key().decrypt(password)
        except:
            pass

        self._manual_password = True
        import getpass as _getpass
        return _getpass.getpass(prompt="Please enter the login password: ")

    def _get_otpcode(self, username, identity_url):
        """Get the OTP code for the passed user on the passed identity
           service url"""
        try:
            userinfo = self._read_userinfo(username, identity_url)

            if userinfo:
                from Acquire.Client import OTP as _OTP
                secret = self._get_wallet_key().decrypt(userinfo["otpsecret"])
                device_uid = userinfo["device_uid"]
                self._manual_otpcode = False
                self._device_uid = device_uid
                return _OTP(secret=secret).generate()
        except:
            pass

        self._manual_otpcode = True
        self._device_uid = None
        import getpass as _getpass
        return _getpass.getpass(
                    prompt="Please enter the one-time-password code: ")

    def add_service(self, service):
        """Add a cached service info for the passed service. If it
           already exists, then this verifies that the added service
           is the same as the previously-seen service
        """
        from Acquire.ObjectStore import string_to_safestring \
            as _string_to_safestring

        service_file = "%s/service_%s" % (
            self._wallet_dir,
            _string_to_safestring(service.canonical_url()))

        existing_service = None

        try:
            existing_service = _read_service(service_file)
        except:
            pass

        if existing_service is not None:
            if service.validation_string() == \
               existing_service.validation_string():
                return service
            elif service.is_evolution_of(existing_service):
                # the service has evolved - this is ok
                _write_service(service, service_file)
                return service
            else:
                reply = _input(
                    "This is a service you have seen before, but "
                    "it has changed?\n\n"
                    "URL = %s (%s)\n"
                    "UID = %s (%s)\n"
                    "public_key fingerprint = %s (%s)\n"
                    "public_certificate fingerprint = %s (%s)\n\n"
                    "verification string = %s (%s)\n\n"
                    "\nDo you trust this updated service? y/n " %
                    (service.canonical_url(),
                     existing_service.canonical_url(),
                     service.uid(), existing_service.uid(),
                     service.public_key().fingerprint(),
                     existing_service.public_key().fingerprint(),
                     service.public_certificate().fingerprint(),
                     existing_service.public_certificate().fingerprint(),
                     service.validation_string(),
                     existing_service.validation_string())
                )

                if reply[0].lower() == 'y':
                    print("Now trusting %s" % str(service))
                else:
                    print("Not trusting this service!")
                    raise PermissionError(
                        "We do not trust the service '%s'" % str(service))

                # We trust the service, so save this for future reference
                _write_service(service, service_file)
                return service

        reply = _input(
                    "This is a new service that you have not seen before.\n\n"
                    "URL = %s\n"
                    "UID = %s\n"
                    "public_key fingerprint = %s\n"
                    "public_certificate fingerprint = %s\n\n"
                    "verification string = %s\n\n"
                    "\nDo you trust this service? y/n " %
                    (service.canonical_url(),
                     service.uid(),
                     service.public_key().fingerprint(),
                     service.public_certificate().fingerprint(),
                     service.validation_string())
                )

        if reply[0].lower() == 'y':
            print("Now trusting %s" % str(service))
        else:
            print("Not trusting this service!")
            raise PermissionError(
                "We do not trust the service '%s'" % str(service))

        # We trust the service, so save this for future reference
        _write_service(service, service_file)

        return service

    def get_services(self):
        """Return all of the trusted services known to this wallet"""
        import glob as _glob
        service_files = _glob.glob("%s/service_*" % self._wallet_dir)

        services = []

        for service_file in service_files:
            services.append(_read_service(service_file))

        return services

    def get_service(self, service_url):
        """Return the service at 'service_url'. This will return the
           cached service if it exists, or will add a new service if
           the user so wishes
        """
        from Acquire.ObjectStore import string_to_safestring \
            as _string_to_safestring

        service_file = "%s/service_%s" % (
            self._wallet_dir,
            _string_to_safestring(service_url))

        existing_service = None

        try:
            existing_service = _read_service(service_file)
        except:
            pass

        if existing_service is not None:
            # check if the keys need rotating - if they do, load up
            # the new keys and save them to the service file...
            if existing_service.should_refresh_keys():
                existing_service.refresh_keys()
                _write_service(existing_service, service_file)

            return existing_service
        else:
            from Acquire.Service import get_remote_service as \
                _get_remote_service

            service = _get_remote_service(service_url)
            return self.add_service(service)

    def remove_all_services(self):
        """Remove all trusted services from this Wallet"""
        import glob as _glob
        import os as _os
        service_files = _glob.glob("%s/service_*" % self._wallet_dir)

        for service_file in service_files:
            if _os.path.exists(service_file):
                _os.unlink(service_file)

        # clear cache to force a new lookup
        from ._service import _cache_service_lookup
        _cache_service_lookup.clear()

    def remove_service(self, service):
        """Remove the cached service info for the passed service"""
        if isinstance(service, str):
            service_url = service
        else:
            service_url = service.canonical_url()

        from Acquire.ObjectStore import string_to_safestring \
            as _string_to_safestring

        service_file = "%s/service_%s" % (
            self._wallet_dir,
            _string_to_safestring(service_url))

        import os as _os

        if _os.path.exists(service_file):
            _os.unlink(service_file)

        # clear cache to force a new lookup
        from ._service import _cache_service_lookup
        _cache_service_lookup.clear()

    def send_password(self, url, username=None, password=None,
                      otpcode=None, remember_password=True,
                      remember_device=None, dryrun=None):
        """Send a password and one-time code to the supplied login url"""
        self._manual_password = False
        self._manual_otpcode = False

        if not remember_password:
            remember_device = False

        # the login URL is of the form "server/code"
        words = url.split("/")
        identity_service = "/".join(words[0:-1])
        short_uid = words[-1].split("=")[-1]

        # now get the service
        service = self.get_service(identity_service)

        if not service.can_identify_users():
            from Acquire.Client import LoginError
            raise LoginError(
                "Service '%s' is unable to identify users! "
                "You cannot log into something that is not "
                "a valid identity service!" % (service))

        if not username:
            # choose a username from any existing files...
            username = self._get_username()

        print("Logging in using username '%s'" % username)
        if password is None:
            password = self._get_user_password(
                                        username=username,
                                        identity_url=service.canonical_url())

        if otpcode is None:
            otpcode = self._get_otpcode(username=username,
                                        identity_url=service.canonical_url())

        print("\nLogging in to '%s', session '%s'..." % (
              service.canonical_url(), short_uid), end="")

        _flush_output()

        if dryrun:
            print("Calling %s with username=%s, password=%s, otpcode=%s, "
                  "remember_device=%s, device_uid=%s, short_uid=%s" %
                  (service.canonical_url(), username, password, otpcode,
                   remember_device, self._device_uid, short_uid))
            return

        try:
            function = "login"
            args = {"username": username,
                    "password": password,
                    "otpcode": otpcode,
                    "remember_device": remember_device,
                    "device_uid": self._device_uid,
                    "short_uid": short_uid}

            response = service.call_function(function=function, args=args)
            print("SUCCEEDED!")
            _flush_output()
        except Exception as e:
            print("FAILED!")
            _flush_output()
            from Acquire.Client import LoginError
            raise LoginError("Failed to log in. %s" % e.args)

        if remember_password:
            try:
                provisioning_uri = response["provisioning_uri"]
            except:
                provisioning_uri = None

            try:
                device_uid = response["device_uid"]
            except:
                device_uid = None

            otpsecret = None

            if provisioning_uri:
                try:
                    otpsecret = _re.search(r"secret=([\w\d+]+)&issuer",
                                           provisioning_uri).groups()[0]
                except:
                    pass

            try:
                user_info = self._read_userinfo(username,
                                                service.canonical_url())
            except:
                user_info = {}

            if user_info is None:
                user_info = {}

            pubkey = self._get_wallet_key().public_key()

            must_write = self._manual_password

            if otpsecret:
                if self._manual_otpcode:
                    must_write = True

            if must_write:
                from Acquire.ObjectStore import string_to_safestring \
                    as _string_to_safestring
                from Acquire.ObjectStore import bytes_to_string \
                    as _bytes_to_string

                user_info["username"] = _string_to_safestring(username)
                user_info["password"] = _bytes_to_string(
                                              pubkey.encrypt(
                                                  password.encode("utf-8")))

                if otpsecret:
                    user_info["otpsecret"] = _bytes_to_string(
                                                pubkey.encrypt(
                                                   otpsecret.encode("utf-8")))
                    user_info["device_uid"] = device_uid

                _write_json(data=user_info, filename=self._get_userfile(
                            username, service.canonical_url()))

        self._manual_password = False
        self._manual_otpcode = False

        return response
