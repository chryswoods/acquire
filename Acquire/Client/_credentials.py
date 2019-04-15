
__all__ = ["Credentials"]


class Credentials:
    @staticmethod
    def encode_password(password, identity_uid, device_uid=None):
        """Simple function that creates an MD5 hash of the password,
           salted using the passed identity_uid and (optionally)
           the device_uid
        """
        from Acquire.Crypto import Hash as _Hash

        if device_uid is not None:
            identity_uid = identity_uid + device_uid

        return _Hash.multi_md5(identity_uid, password)

    @staticmethod
    def package(identity_uid, short_uid, username, password, otpcode,
                device_uid=None):
        """Package up the passed credentials so that they can be sent
           to a server for verification. We employ the following
           steps to make it harder for someone to steal the user's
           password:

            1. An MD5 of the password ("password") is generated, salted with
               the UID of the identity service ("identity_uid"), and,
               optionally, the UID of this device ("device_uid")

            2. A symmetric key is generated from the combined MD5s
               of the user's login name (username) and the short UID of
               this login session (short_uid). This is used to encrypt
               the MD5's password and one-time password code ("otpcode").
               The username and session UID are not sent to the server,
               so an attacker must know what these are to extract
               this information.

            3. Also remember that all communication with a service is
               encrypted using the service's public key, and tranmission
               of data should also be sent over HTTPs.
        """
        from Acquire.Crypto import Hash as _Hash
        from Acquire.Crypto import SymmetricKey as _SymmetricKey
        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string

        encoded_password = Credentials.encode_password(
                                            identity_uid=identity_uid,
                                            device_uid=device_uid,
                                            password=password)

        # if the device_uid is not set, then create a random one
        # so that an attacker does not know...
        if device_uid is None:
            from Acquire.ObjectStore import create_uuid as _create_uuid
            device_uid = _create_uuid()

        data = [encoded_password, device_uid, otpcode]
        string_data = "*".join(data)

        uname_shortid = _Hash.md5(username) + _Hash.md5(short_uid)

        data = _SymmetricKey(symmetric_key=uname_shortid).encrypt(string_data)

        return _bytes_to_string(data)

    @staticmethod
    def unpackage(data, username, short_uid, random_sleep=150):
        """Unpackage the credentials data packaged using "package" above,
           assuming that this data was packaged for the user login
           name "username" and for the session with short UID "short_uid".

           This will return a dictionary containing:

           username: Login name of the user
           short_uid: Short UID of the login session
           device_uid: UID of the login device (this will be random if it
                       was not set by the user)
           password: The MD5 of the password, salted using the UID of the
                     identity service, and optionally the device_uid
           otpcode: The one-time-password code for this login

           To make timing-based attacks harder, you can set 'random_sleep'
           to add an additional random sleep of up to 'random_sleep'
           milliseconds onto the end of the unpackage function
        """
        from Acquire.Crypto import Hash as _Hash
        from Acquire.Crypto import SymmetricKey as _SymmetricKey
        from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

        data = _string_to_bytes(data)

        uname_shortid = _Hash.md5(username) + _Hash.md5(short_uid)

        data = _SymmetricKey(symmetric_key=uname_shortid).decrypt(data)

        data = data.split("*")

        result = {"username": username,
                  "short_uid": short_uid,
                  "device_uid": data[1],
                  "password": data[0],
                  "otpcode": data[2]}

        if random_sleep is not None:
            import random as _random
            import time as _time
            random_sleep = _random.randint(0, random_sleep)
            _time.sleep(0.001 * random_sleep)

        return result
