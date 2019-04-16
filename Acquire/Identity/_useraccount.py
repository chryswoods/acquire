
__all__ = ["UserAccount"]

_user_root = "identity/users"


def _encode_username(username):
    """This function returns an encoded (sanitised) version of
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

    def __init__(self, username=None, user_uid=None,
                 private_key=None, status=None):
        """Construct from the passed username"""
        self._username = username
        self._uid = user_uid
        self._privkey = private_key
        self._status = status

    @staticmethod
    def create(username, password):
        """Create a new account with username 'username', which will
           be secured using the passed password.

           Note that this will create an account with a specified
           user UID, meaning that different users can have the same
           username. We identify the right user via the combination
           of username, password and OTP code.

           This returns a tuple of the user_uid and OTP for the
           newly-created account
        """
        # create a UID for this new user
        from Acquire.ObjectStore import create_uuid as _create_uuid
        user_uid = _create_uuid()

        # now create the primary password for this user and use
        # this to encrypt the special keys for this user
        from Acquire.Crypto import PrivateKey

        privkey = PrivateKey(auto_generate=True)
        primary_password = PrivateKey.random_passphrase()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.Service import get_service_public_key \
            as _get_service_public_key
        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
        from Acquire.Identity import UserCredentials as _UserCredentials

        bucket = _get_service_account_bucket()

        # now create the credentials used to validate a login
        otp = _UserCredentials.create(user_uid=user_uid,
                                      password=password,
                                      primary_password=primary_password)

        # create the user account
        user = UserAccount(username=username, user_uid=user_uid,
                           private_key=privkey, status="active")

        # now save a lookup from the username to this user_uid
        # (many users can have the same username). Use this lookup
        # to hold a recovery password for this account
        service_pubkey = _get_service_public_key()
        recovery_password = _bytes_to_string(
                                service_pubkey.encrypt(primary_password))

        key = "%s/names/%s/%s" % (_user_root, user.encoded_name(), user_uid)
        _ObjectStore.set_string_object(bucket=bucket, key=key,
                                       string_data=recovery_password)

        # finally(!) save the account itself to the object store
        key = "%s/uids/%s" % (_user_root, user_uid)
        data = user.to_data(passphrase=primary_password)
        _ObjectStore.set_object_from_json(bucket=bucket,
                                          key=key,
                                          data=data)

        # return the OTP and user_uid
        return (user_uid, otp)

    @staticmethod
    def login(credentials, user_uid=None, remember_device=False):
        """Login to the session with specified 'short_uid' with the
           user with passed 'username' and 'credentials',
           optionally specifying the user_uid
        """
        if user_uid is None:
            # find all of the user_uids of accounts with this username
            from Acquire.ObjectStore import ObjectStore as _ObjectStore
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket

            bucket = _get_service_account_bucket()

            encoded_name = _encode_username(credentials.username())
            prefix = "%s/names/%s/" % (_user_root, encoded_name)

            try:
                names = _ObjectStore.get_all_object_names(bucket=bucket,
                                                          prefix=prefix)
            except:
                names = []

            user_uids = []
            for name in names:
                user_uids.append(name.split("/")[-1])
        else:
            user_uids = [user_uid]

        if len(user_uids) == 0:
            from Acquire.Identity import UserValidationError
            raise UserValidationError("No user with name '%s'" %
                                      credentials.username())

        from Acquire.Identity import UserCredentials as _UserCredentials
        return _UserCredentials.login(credentials=credentials,
                                      user_uids=user_uids,
                                      remember_device=remember_device)

    def __str__(self):
        return "UserAccount(name : %s)" % self._username

    def name(self):
        """Return the name of this account"""
        return self._username

    def username(self):
        """Synonym for 'name'"""
        return self.name()

    def encoded_name(self):
        """Return the encoded (sanitised) username"""
        return _encode_username(self._username)

    def uid(self):
        """Return the globally unique ID for this account"""
        return self._uid

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
        return self._privkey.public_key()

    def private_key(self):
        """Return the lines of the private key for this account"""
        return self._privkey

    def status(self):
        """Return the status for this account"""
        if self._status is None:
            return "invalid"

        return self._status

    def to_data(self, passphrase, mangleFunction=None):
        """Return a data representation of this object (dictionary)"""
        if self._username is None:
            return None

        data = {}
        data["username"] = self._username
        data["status"] = self._status
        data["uid"] = self._uid
        data["private_key"] = self._privkey.to_data(
                                        passphrase=passphrase,
                                        mangleFunction=mangleFunction)

        return data

    @staticmethod
    def from_data(data, passphrase, mangleFunction=None):
        """Return a UserAccount constructed from the passed
           data (dictionary)
        """

        user = UserAccount()

        if data is not None and len(data) > 0:
            from Acquire.Crypto import PrivateKey as _PrivateKey

            user._username = data["username"]
            user._status = data["status"]
            user._uid = data["uid"]
            user._privkey = _PrivateKey.from_data(
                                            data=data["private_key"],
                                            passphrase=passphrase,
                                            mangleFunction=mangleFunction)

        return user
