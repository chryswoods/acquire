
__all__ = ["UserCredentials"]

_user_root = "identity/users"


class UserCredentials:
    """This class is used to store user credentials in the object
       store, and to verify that user credentials are correct.

       The user credentials are used to ultimately store a
       primary password for the user, which unlocks the user's
       primary private key
    """
    def __init__(self):
        """Construct a null set of UserCredentials"""
        self._primary_password = None
        self._privkey = None
        self._otp = None

    def is_null(self):
        """Return whether or not these credentials are null"""
        return self._primary_password is None

    def is_locked(self):
        """Return whether or not these credentials are locked"""
        from Acquire.Crypto import PrivateKey as _PrivateKey
        return not isinstance(self._privkey, _PrivateKey)

    def is_unlocked(self):
        """Return whether or not these credentials are unlocked"""
        return not self.is_locked()

    def lock(self, password):
        """Lock these credentials using the passed password"""
        if self.is_locked():
            return

        pubkey = self._privkey.public_key()
        self._otp = self._otp.encrypt(pubkey)
        self._primary_password = pubkey.encrypt(self._primary_password)
        self._privkey = self._privkey.to_data(passphrase=password)

    def unlock(self, password):
        """Unlock these credentials using the passed password"""
        if self.is_unlocked():
            return

        from Acquire.Crypto import PrivateKey as _PrivateKey
        from Acquire.Crypto import OTP as _OTP

        try:
            self._privkey = _PrivateKey.from_data(data, passphrase=password)
        except:
            from Acquire.Identity import UserValidationError
            raise UserValidationError("Incorrect password")

        self._otp = _OTP.decrypt(secret=self._otp, key=self._privkey)
        self._primary_password = self._privkey.decrypt(self._primary_password)

    @staticmethod
    def hash(username, password, service_uid=None):
        """Return a secure hash of the passed username and password"""
        from Acquire.Crypto import Hash as _Hash
        from Acquire.Service import get_this_service as _get_this_service

        if service_uid is None:
            service_uid = _get_this_service(need_private_access=False).uid()

        result = _Hash.multi_md5(service_uid, username+password)

        return result

    @staticmethod
    def list_devices(user_uid):
        """Return a list of devices that the user has "remembered"
           as being safe to log in from. These devices will not need
           to use a user-visible OTP code
        """
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()
        device_key = "%s/credentials/%s" % (_user_root, user_uid)

        devices = _ObjectStore.get_all_objects(bucket=bucket,
                                               prefix=device_key)

        return devices

    @staticmethod
    def recover_otp(user_uid, password, reset_otp=False):
        """Recover the OTP secret for the user with passed user_uid
           logging in via the specified password. This will return
           the OTP for the this user. If 'reset_otp' is True,
           then the original OTP will be replaced by a new OTP,
           which will then be returned
        """
        creds = UserCredentials.load(user_uid=user_uid)
        creds.unlock(password)

        otp = creds._otp

        if reset_otp:
            from Acquire.Crypto import OTP as _OTP
            otp = _OTP()
            creds._otp = otp
            creds.lock(password)
            creds.save(user_uid=user_uid)

        return otp

    @staticmethod
    def create(user_uid, password, primary_password,
               device_uid=None):
        """Create the credentials for the user with specified
           user_uid, optionally logging in via the specified
           device_uid, using the specified password, to protect
           the passed "primary_password"

           This returns the OTP that has been created to be
           associated with these credentials
        """
        from Acquire.Crypto import PrivateKey as _PrivateKey
        from Acquire.Crypto import OTP as _OTP

        if device_uid is None:
            device_uid = user_uid

        creds = UserCredentials()

        creds._privkey = _PrivateKey(name="user_creds_key %s" % user_uid)
        otp = _OTP()
        creds._otp = otp
        creds._primary_password = primary_password

        creds.lock(password=password)
        creds.save(user_uid=user_uid, device_uid=device_uid)

        return otp

    def verify(self, user_uid, device_uid, otpcode):
        """Verify that the passed otpcode is valid and has not been used
           before for this user_uid and device_uid combination
        """
        if self.is_locked():
            raise PermissionError("Cannot verify a locked set of credentials!")

        self._otp.verify(otpcode=otpcode)

        # the code is correct, but has it been used before? If so, then
        # we may be suffering a replay attack!
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.ObjectStore import get_datetime_now as _get_datetime_now
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        now = _get_datetime_now()
        bucket = _get_service_account_bucket()

        if device_uid is None:
            device_uid = user_uid

        key = "%s/otpcodes/%s/%s/%s" % (_user_root, user_uid,
                                        device_uid, otpcode)

        try:
            data = _ObjectStore.get_string_object(bucket=bucket, key=key)
        except:
            data = None

        if data is not None:
            from Acquire.ObjectStore import string_to_datetime \
                as _string_to_datetime
            old = _string_to_datetime(data)

            if (old - now).total_seconds() < 240:
                from Acquire.Crypto import RepeatedOTPCodeError
                raise RepeatedOTPCodeError(
                    "You cannot re-use the same OTP code. Please wait "
                    "a minute to get a new code, and then try again. "
                    "If you haven't used this code, then somebody "
                    "may be trying to hack your account.")
        else:
            # save the new time of using this code
            from Acquire.ObjectStore import datetime_to_string \
                as _datetime_to_string
            data = _datetime_to_string(now)
            _ObjectStore.set_string_object(bucket=bucket, key=key,
                                            string_data=data)

    @staticmethod
    def login(credentials, user_uids, remember_device=False):
        """Verify the passed credentials are correct.
           This will find the account
           that matches these credentials. If one does, then this
           will validate the credentials are correct, and then return
           a tuple of the (user_uid, primary_password) for that
           user
        """
        from Acquire.Client import Credentials as _Credentials
        from Acquire.Crypto import RepeatedOTPCodeError \
            as _RepeatedOTPCodeError

        if not isinstance(credentials, _Credentials):
            raise TypeError("The passed credentials must be type Credentials")

        username = credentials.username()
        short_uid = credentials.short_uid()
        device_uid = credentials.device_uid()
        password = credentials.password()
        otpcode = credentials.otpcode()

        # now try to find a matching user_uid and verify that the
        # password and otpcode are correct
        verified_user_uid = None
        verified_device_uid = None
        verified_creds = None

        for user_uid in user_uids:
            matched_device_uid = None

            try:
                creds = UserCredentials.load(user_uid=user_uid,
                                             device_uid=device_uid)
                matched_device_uid = device_uid
            except:
                creds = None

            if creds is None:
                try:
                    # unknown device_uid. Try using the user_uid
                    creds = UserCredentials.load(user_uid=user_uid)
                except:
                    creds = None

            if creds is not None:
                # verify the credentials
                try:
                    creds.unlock(password=password)
                    creds.verify(user_uid=user_uid, device_uid=device_uid,
                                 otpcode=otpcode)
                    verified_creds = creds
                    verified_user_uid = user_uid
                    verified_device_uid = matched_device_uid
                    break
                except _RepeatedOTPCodeError as e:
                    # if the OTP code is entered twice, then we need
                    # to invalidate the other session
                    print(e)
                    raise e
                except Exception as e:
                    # this is not the matching user...
                    print("ERROR %s" % e)
                    pass

        print("I AM HERE %s" % verified_creds)

        if verified_creds is not None:
            # everything is ok - we can load the user account via the
            # decrypted primary password
            creds = verified_creds
            user_uid = verified_user_uid
            device_uid = verified_device_uid
            otp = creds._otp

            from Acquire.Identity import UserAccount as _UserAccount

            user = _UserAccount.load(user_uid=user_uid,
                                     passphrase=creds._primary_password)

            if user.uid() != user_uid:
                from Acquire.Identity import UserValidationError
                raise UserValidationError(
                    "Unable to validate user as mismatch in user_uids!")

            if device_uid is None and remember_device:
                # create a new OTP that is unique for this device
                from Acquire.ObjectStore import ObjectStore as _ObjectStore
                from Acquire.ObjectStore import create_uid as _create_uid
                from Acquire.Service import get_service_account_bucket \
                    as _get_service_account_bucket
                from Acquire.Client import Credentials as _Credentials

                bucket = _get_service_account_bucket()
                device_uid = _create_uid()
                device_password = _Credentials.encode_device_uid(
                                                    encoded_password=password,
                                                    device_uid=device_uid)

                otp = UserCredentials.create(
                                    user_uid=user_uid,
                                    password=device_password,
                                    primary_password=creds._primary_password,
                                    device_uid=device_uid)

                # now save a lookup so that we can find the user_uid from
                # the username and device-specific password
                encoded_password = UserCredentials.hash(
                                            username=username,
                                            password=device_password)

                key = "%s/passwords/%s/%s" % (_user_root, encoded_password,
                                              user_uid)

                from Acquire.ObjectStore import get_datetime_now_to_string \
                    as _get_datetime_now_to_string

                _ObjectStore.set_string_object(
                                    bucket=bucket, key=key,
                                    string_data=_get_datetime_now_to_string())

            return {"user": user, "otp": otp, "device_uid": device_uid}

        else:
            # only get here if there are no matching users (or the
            # user-supplied password etc. are wrong)
            from Acquire.Identity import UserValidationError
            raise UserValidationError(
                "Invalid credentials logging into session '%s' "
                "with username '%s'" % (short_uid, username))

    def save(self, user_uid, device_uid=None):
        """Save this set of credentials to the ObjectStore for the specified
           user_uid and (optionally) device_uid
        """
        if device_uid is None:
            device_uid = user_uid

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        key = "%s/credentials/%s/%s" % (_user_root, user_uid, device_uid)

        bucket = _get_service_account_bucket()
        _ObjectStore.set_object_from_json(bucket=bucket, key=key,
                                          data=self.to_data())

    @staticmethod
    def load(user_uid, device_uid=None):
        """Load the credentials for the passed user_uid and
           (optionally) device_uid
        """
        if device_uid is None:
            device_uid = user_uid

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        key = "%s/credentials/%s/%s" % (_user_root, user_uid, device_uid)

        bucket = _get_service_account_bucket()

        try:
            data = _ObjectStore.get_object_from_json(bucket=bucket, key=key)
        except:
            data = None

        if data is None:
            if user_uid == device_uid:
                raise PermissionError(
                    "There is no account associated with user_uid %s" %
                    user_uid)
            else:
                raise PermissionError(
                    "There is no device for user_uid %s with device_uid %s" %
                    (user_uid, device_uid))

        return UserCredentials.from_data(data)

    def to_data(self):
        """Return a json-serialisable dictionary for this object"""

        if self.is_null():
            return {}

        if self.is_unlocked():
            raise PermissionError(
                "You must lock the credentials before saving!")

        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string

        data = {}

        data["primary_password"] = _bytes_to_string(self._primary_password)
        data["privkey"] = self._privkey
        data["otp"] = _bytes_to_string(self._otp)

        return data

    @staticmethod
    def from_data(data):
        """Return a UserCredentials created from the passed json-deserialised
           dictionary
        """

        if data is None or len(data) == 0:
            return UserCredentials()

        from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

        creds = UserCredentials()

        creds._primary_password = data["primary_password"]
        creds._privkey = data["prikey"]
        creds._otp = _string_to_bytes(data["otp"])

        return creds
