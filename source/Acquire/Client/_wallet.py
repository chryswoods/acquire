
import os as _os
import sys as _sys
import getpass as _getpass
import glob as _glob
import re as _re
import base64 as _base64
import lazy_import as _lazy_import

from Acquire.Service import call_function as _call_function
from Acquire.Service import pack_arguments as _pack_arguments
from Acquire.Service import unpack_arguments as _unpack_arguments
from Acquire.Service import Service as _Service

from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import OTP as _OTP
from Acquire.Crypto import get_private_key as _get_private_key

from ._errors import LoginError

_pyotp = _lazy_import.lazy_module("pyotp")

__all__ = ["Wallet"]


class Wallet:
    """This class holds a wallet that can be used to simplify
       sending passwords and one-time-password (OTP) codes
       to an acquire identity service.

       This holds a wallet of passwords and (optionally)
       OTP secrets that are encrypted using a local keypair
       that is unlocked by a password supplied by the user locally.
    """
    def __init__(self):
        self._wallet_key = None
        self._get_wallet_key()
        self._cache = {}
        self._service_info = {}
        self._manual_password = False
        self._manual_otpcode = False

    @staticmethod
    def _wallet_dir():
        """Directory containing all of the wallet files"""
        homedir = _os.path.expanduser("~")

        walletdir = "%s/.acquire" % homedir

        if not _os.path.exists(walletdir):
            _os.mkdir(walletdir)

        return walletdir

    def _create_wallet_key(self, filename):
        """Create a new wallet key for the user"""

        password = _getpass.getpass(
                     prompt="Please enter a password to encrypt your wallet: ")

        key = _PrivateKey()

        bytes = key.bytes(password)

        password2 = _getpass.getpass(prompt="Please confirm the password: ")

        if password != password2:
            print("The passwords don't match. Please try again.")
            self._create_wallet_key(filename)
            return

        # the passwords match - write this to the file
        with open(filename, "wb") as FILE:
            FILE.write(bytes)

        return key

    def _get_wallet_key(self):
        """Return the private key used to encrypt everything in the wallet.
           This will ask for the users password
        """
        if self._wallet_key:
            return self._wallet_key

        wallet_dir = Wallet._wallet_dir()

        keyfile = "%s/wallet_key.pem" % wallet_dir

        if not _os.path.exists(keyfile):
            self._wallet_key = self._create_wallet_key(keyfile)
            return self._wallet_key

        # read the keyfile and decrypt
        with open(keyfile, "rb") as FILE:
            bytes = FILE.read()

        # get the user password
        wallet_key = None
        while not wallet_key:
            password = _getpass.getpass(
                            prompt="Please enter your wallet password: ")

            try:
                wallet_key = _PrivateKey.read_bytes(bytes, password)
            except:
                print("Invalid password. Please try again.")

        self._wallet_key = wallet_key
        return wallet_key

    @staticmethod
    def _get_userfile(username, identity_url):
        """Return the userfile for the passed username logging into the
           passed identity url"""
        return "%s/user_%s_%s_encrypted" % (
            Wallet._wallet_dir(),
            _base64.b64encode(username.encode("utf-8")).decode("utf-8"),
            _base64.b64encode(identity_url.encode("utf-8")).decode("utf-8"))

    @staticmethod
    def remove_user_info(username):
        """Call this function to remove the userinfo associated
           with the account 'username' for all identity services
        """
        wallet_dir = Wallet._wallet_dir()

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

        if not _os.path.exists(filename):
            return

        with open(filename, "rb") as FILE:
            data = _unpack_arguments(FILE.read())

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
        return self._read_userfile(Wallet._get_userfile(username,
                                                        identity_url))

    def _get_username(self):
        """Function to find a username automatically, of if that fails,
           to ask the user
        """
        wallet_dir = Wallet._wallet_dir()

        userfiles = _glob.glob("%s/user_*_encrypted" % wallet_dir)

        userinfos = {}

        for userfile in userfiles:
            try:
                userinfo = self._read_userfile(userfile)
                userinfos[userinfo["username"]] = userinfo
            except:
                pass

        usernames = list(userinfos.keys())
        usernames.sort()

        if len(usernames) == 1:
            return usernames[0]

        if len(usernames) == 0:
            print("Please type your username: ", end="")
            _sys.stdout.flush()
            return _sys.stdin.readline()[0:-1]

        print("Please choose the account by typing in its number, "
              "or type a new username if you want a different account.")

        for (i, username) in enumerate(usernames):
            print("[%d] %s" % (i+1, username))

        username = None

        while not username:
            print("Make your selection: ", end="")
            _sys.stdout.flush()

            input = _sys.stdin.readline()[0:-1]

            try:
                input = int(input) - 1
                if input < 0 or input >= len(usernames):
                    print("Invalid account. Try again...")
                else:
                    username = usernames[input]
            except:
                username = input

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
                return self._wallet_key.decrypt(password)
        except:
            pass

        self._manual_password = True
        return _getpass.getpass(prompt="Please enter the login password: ")

    def _get_otpcode(self, username, identity_url):
        """Get the OTP code for the passed user on the passed identity
           service url"""
        try:
            userinfo = self._read_userinfo(username, identity_url)

            if userinfo:
                secret = self._wallet_key.decrypt(userinfo["otpsecret"])
                device_uid = userinfo["device_uid"]
                self._manual_otpcode = False
                self._device_uid = device_uid
                return _pyotp.totp.TOTP(secret).now()
        except:
            pass

        self._manual_otpcode = True
        self._device_uid = None
        return _getpass.getpass(
                    prompt="Please enter the one-time-password code: ")

    @staticmethod
    def remove_service_info(identity_service):
        """Remove the cached service info for the passed service"""
        service_file = "%s/service_%s" % (
            Wallet._wallet_dir(),
            _base64.b64encode(
                identity_service.encode("utf-8")).decode("utf-8"))

        if _os.path.exists(service_file):
            _os.unlink(service_file)

    def _get_service_info(self, identity_service):
        """Return the service info for the passed identity service"""
        try:
            return self._service_info[identity_service]
        except:
            pass

        # can we read this from a file?
        service_file = "%s/service_%s" % (
            Wallet._wallet_dir(),
            _base64.b64encode(
                identity_service.encode("utf-8")).decode("utf-8"))

        try:
            with open(service_file, "rb") as FILE:
                service_info = _Service.from_data(
                                    _unpack_arguments(FILE.read()))
                self._service_info[identity_service] = service_info
                return service_info
        except:
            pass

        try:
            key = _get_private_key("function")
            response = _call_function(identity_service, response_key=key)
            service = _Service.from_data(response["service_info"])
        except Exception as e:
            raise LoginError(
                "Error connecting to the login service %s: Error = %s" %
                (identity_service, str(e)))

        if not service.is_identity_service():
            raise LoginError(
                "You cannot log into something that is not "
                "a valid identity service!")

        self._service_info[identity_service] = service

        # save this for future reference
        with open(service_file, "wb") as FILE:
            FILE.write(_pack_arguments(service.to_data()))

        return service

    def _get_service_key(self, identity_service):
        """Return the public encryption key for the passed identity service"""
        return self._get_service_info(identity_service).public_key()

    def _get_service_cert(self, identity_service):
        """Return the public signing certificaet for
           the passed identity service
        """
        return self._get_service_info(identity_service).public_certificate()

    def send_password(self, url, username=None, remember_password=True,
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

        # get the public key of this identity service
        service_key = self._get_service_key(identity_service)
        service_cert = self._get_service_cert(identity_service)

        if not username:
            # choose a username from any existing files...
            username = self._get_username()

        print("Logging in using username '%s'" % username)
        password = self._get_user_password(username, identity_service)
        otpcode = self._get_otpcode(username, identity_service)

        print("\nLogging in to '%s', session '%s'..." % (
              identity_service, short_uid), end="")
        _sys.stdout.flush()

        if dryrun:
            print("Calling %s with username=%s, password=%s, otpcode=%s, "
                  "remember_device=%s, device_uid=%s, short_uid=%s" %
                  (identity_service, username, password, otpcode,
                   remember_device, self._device_uid, short_uid))
            return

        try:
            key = _get_private_key("function")
            response = _call_function(identity_service, "login",
                                      args_key=service_key, response_key=key,
                                      public_cert=service_cert,
                                      username=username, password=password,
                                      otpcode=otpcode,
                                      remember_device=remember_device,
                                      device_uid=self._device_uid,
                                      short_uid=short_uid)
            print("SUCCEEDED!")
            _sys.stdout.flush()
        except Exception as e:
            print("FAILED!")
            _sys.stdout.flush()
            raise LoginError("Failed to log in: %s" % str(e))

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
                user_info = self._read_userinfo(username, identity_service)
            except:
                user_info = {}

            if user_info is None:
                user_info = {}

            pubkey = self._wallet_key.public_key()

            must_write = self._manual_password

            if otpsecret:
                if self._manual_otpcode:
                    must_write = True

            if must_write:
                user_info["username"] = username.encode(
                                            "utf-8").decode("utf-8")
                user_info["password"] = _bytes_to_string(
                                              pubkey.encrypt(
                                                  password.encode("utf-8")))

                if otpsecret:
                    user_info["otpsecret"] = _bytes_to_string(
                                                pubkey.encrypt(
                                                   otpsecret.encode("utf-8")))
                    user_info["device_uid"] = device_uid

                packed_data = _pack_arguments(user_info)

                with open(Wallet._get_userfile(
                          username, identity_service), "wb") as FILE:
                    FILE.write(packed_data)

        self._manual_password = False
        self._manual_otpcode = False

        return response
