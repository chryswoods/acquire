
__all__ = ["UserAccount"]

_user_root = "identity/users"


def _sanitise_username(username):
    """This function returns a sanitised version of
        the username. This will ensure that the username
        is valid (must be between 3 and 50 characters).
        The sanitised username is the encoded version,
        meaning that a user can use a unicode (emoji)
        username if they so desire
    """
    if username is None:
        return None

    if len(username) < 3 or len(username) > 150:
        from Acquire.Identity import UsernameError
        raise UsernameError(
            "The username must be between 3 and 150 characters!")

    from Acquire.ObjectStore import string_to_encoded \
        as _string_to_encoded

    return _string_to_encoded(username)


class UserAccount:
    """This class holds all information about a user's account,
       e.g. their username, the sanitised username for the person
       on the system, their account keys, status etc.

       This data can be serialised to an from json to allow
       easy saving a retrieval from an object store
    """

    def __init__(self, username=None):
        """Construct from the passed username"""
        self._username = username
        self._sanitised_username = UserAccount.sanitise_username(username)
        self._privkey = None
        self._pubkey = None
        self._uid = None

        if username is None:
            self._status = None
        else:
            self._status = "disabled"

    @staticmethod
    def create(username, password):
        """Create a new account with username 'username', which will
           be secured using the passed password. This will return
           an OTP that must be returned to the user so that they
           can setup their OTP generator.

           Note that this will create an account with a specified
           user UID, meaning that different users can have the same
           username. We identify the right user via the combination
           of username, password and OTP code
        """
        sanitised_username = _sanitise_username(username)

        # create a UID for this new user
        from Acquire.ObjectStore import create_uuid as _create_uuid
        user_uid = _create_uuid()

        # now create the primary password for this user and use
        # this to encrypt the special keys for this user
        from Acquire.Crypto import PrivateKey

        privkey = PrivateKey(auto_generate=True)
        primary_password = PrivateKey.random_passphrase()
        privkey_data = privkey.to_data(passphrase=primary_password)

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.Service import get_service_public_key \
            as _get_service_public_key
        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string

        bucket = _get_service_account_bucket()

        user_root = "%s/%s" % (_user_root, user_uid)

        # save a recovery password for this user
        service_pubkey = _get_service_public_key()
        recovery_password = _bytes_to_string(
                                service_pubkey.encrypt(primary_password))
        _ObjectStore.set_string_object(bucket=bucket,
                                       key="%s/recovery_password",
                                       value=recovery_password)

        data = {"username": username,
                "private_key": privkey_data,
                "public_key": privkey.public_key.to_data()
                }

        _ObjectStore.set_object_from_json(bucket=bucket,
                                          key="%s/details",
                                          value=data)

        # now create the credentials used to validate a login


    def __str__(self):
        return "UserAccount( name : %s )" % self._username

    def name(self):
        """Return the name of this account"""
        return self._username

    def username(self):
        """Synonym for 'name'"""
        return self.name()

    def sanitised_name(self):
        """Return the sanitised username"""
        return self._sanitised_username

    def uid(self):
        """Return the globally unique ID for this account"""
        return self._uid

    def max_open_sessions(self):
        """Return the maximum number of open login sessions
           (and open login requests) allowed for this user account"""
        return 10

    def login_request_timeout(self):
        """Return the number of seconds a login request will
           remain active. This should normally be short, e.g. 30 minutes"""
        return 1800

    def login_timeout(self):
        """Return the maximum number of seconds a single login
           can remain active. This should normally be of the order
           of 1-7 days, as individual calculations or workflows
           should not normally take longer than this"""
        return 7 * 24 * 3600

    def login_root_url(self):
        """Return the root URL used to log into this account"""
        from Acquire.Service import get_this_service as _get_this_service
        return _get_this_service().canonical_url()

    def is_valid(self):
        """Return whether or not this is a valid account"""
        return not (self._status is None)

    def is_active(self):
        """Return whether or not this is an active account"""
        if self._status is None:
            return False
        else:
            return self._status == "active"

    def public_key(self):
        """Return the lines of the public key for this account"""
        return self._pubkey

    def private_key(self):
        """Return the lines of the private key for this account"""
        return self._privkey

    def status(self):
        """Return the status for this account"""
        if self._status is None:
            return "invalid"

        return self._status

    def generate
        """Set the private and public keys for this account. The
           keys can be set from files or from a binary read file..
        """
        if self._status is None or privkey is None or pubkey is None:
            return

        try:
            privkey = open(privkey, "rb").read()
        except:
            pass

        try:
            pubkey = open(pubkey, "rb").read()
        except:
            pass

        self._privkey = privkey
        self._pubkey = pubkey

        if self._uid is None:
            # generate the uid now, as this should not happen until
            # the account has been first activated. After this point,
            # the uuid of the account should not change
            from Acquire.ObjectStore import create_uuid as _create_uuid
            self._uid = _create_uuid()

        self._status = "active"

    def reset_password(self, password):
        """Call this function to reset the password of this account.
           Note that this will reset the password
        """
        from Acquire.Crypto import PrivateKey as _PrivateKey

        privkey = _PrivateKey()
        pubkey = privkey.public_key()

        self.set_keys(privkey.bytes(password), pubkey.bytes())

        return otp

    def validate_password(self, password, otpcode, remember_device=False,
                          device_secret=None):
        """Validate that the passed password and one-time-code are valid.
           If they are, then do nothing. Otherwise raise an exception.
           If 'remember_device' is true, then this returns the provisioning
           uri needed to initialise the OTP code for this account
        """
        if not self.is_active():
            from Acquire.Identity import UserValidationError
            raise UserValidationError(
                "Cannot validate against an inactive account")

        from Acquire.Crypto import PrivateKey as _PrivateKey
        from Acquire.Crypto import OTP as _OTP

        # see if we can decrypt the private key using the password
        privkey = _PrivateKey.read_bytes(self._privkey, password)

        if device_secret:
            # decrypt the passed device secret and check the supplied
            # otpcode for that...
            from Acquire.ObjectStore import string_to_bytes as _string_to_bytes
            otp = _OTP.decrypt(_string_to_bytes(device_secret), privkey)
            otp.verify(otpcode)
        else:
            # now decrypt the secret otp and validate the supplied otpcode
            otp = _OTP.decrypt(self._otp_secret, privkey)
            otp.verify(otpcode)

        if remember_device:
            # create a new OTP that is unique for this device and return
            # this together with the provisioning code
            from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
            otp = _OTP()
            otpsecret = _bytes_to_string(otp.encrypt(privkey.public_key()))
            return (otpsecret, otp.provisioning_uri(self.username()))

    def to_data(self):
        """Return a data representation of this object (dictionary)"""
        if self._username is None:
            return None

        data = {}
        data["username"] = self._username
        data["status"] = self._status
        data["uuid"] = self._uuid

        # the keys and secret are arbitrary binary data.
        # These need to be base64 encoded and then turned into strings
        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
        data["private_key"] = _bytes_to_string(self._privkey)
        data["public_key"] = _bytes_to_string(self._pubkey)
        data["otp_secret"] = _bytes_to_string(self._otp_secret)

        return data

    @staticmethod
    def from_data(data):
        """Return a UserAccount constructed from the passed
           data (dictionary)
        """

        if data is None:
            return None

        from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

        user_account = UserAccount(data["username"])
        user_account._privkey = _string_to_bytes(data["private_key"])
        user_account._pubkey = _string_to_bytes(data["public_key"])
        user_account._status = data["status"]
        user_account._uuid = data["uuid"]

        try:
            user_account._otp_secret = _string_to_bytes(data["otp_secret"])
        except:
            user_account._otp_secret = None

        return user_account
