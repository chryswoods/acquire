
__all__ = ["UserCredentials"]

_user_root = "identity/users"


class UserCredentials:
    """This class is used to store user credentials in the object
       store, and to verify that user credentials are correct.

       The user credentials are used to ultimately store a
       primary password for the user, which unlocks the user's
       primary private key
    """
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
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string

        if device_uid is None:
            device_uid = user_uid

        privkey = _PrivateKey(auto_generate=True)
        otp = _OTP()
        otpsecret = otp.encrypt(privkey.public_key())
        primary_secret = privkey.encrypt(primary_password)

        data = {"primary_secret": _bytes_to_string(primary_secret),
                "privkey": privkey.to_data(passphrase=password),
                "otpsecret": _bytes_to_string(otpsecret)
                }

        key = "%s/%s/%s/credentials" % (_user_root, user_uid, device_uid)

        bucket = _get_service_account_bucket()
        _ObjectStore.set_object_from_json(bucket=bucket,
                                          key=key,
                                          data=data)

        if issuer is None:
            issuer = "Acquire"

        return otp

    @staticmethod
    def verify(username, short_uid, credentials):
        """Verify the passed credentials are correct for the specified
           username and short_uid session. This will find the account
           that matches these credentials. If one does, then this
           will validate the credentials are correct, and then return
           a tuple of the (user_uid, primary_password) for that
           user
        """
        do some work here
