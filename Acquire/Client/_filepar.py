

class FilePAR:
    """This class holds a pre-authenticated request to upload
       or download a file. Anyone who holds a copy of this
       object can perform operations authorised on this
       file
    """
    def __init__(self, identifier=None, user=None, aclrule=None,
                 encrypt_key=None, expires_datetime=None):
        """Construct a FilePAR for the specified identifier,
           authorised by the passed user, giving permissions
           according to the passed 'aclrule' (default is
           ACLRule.reader()).

           If 'encrypt_key' is passed, then the FilePAR will
           be encrypted using the passed key.

           The passed 'expires_datetime' is the time at which
           this FilePAR will expire (by default within 24 hours)
        """
        if identifier is None:
            self._identifier = None
            return

        from Acquire.Client import Identifier as _Identifier
        if not isinstance(identifier, _Identifier):
            raise TypeError("The identifier must be type Identifier")

        if identifier.is_null():
            self._identifier = None
            return

        from Acquire.Client import User as _User
        if not isinstance(user, _User):
            raise TypeError("The user must be type User")

        if not user.is_logged_in():
            raise PermissionError("The passed User must be logged in!")

        from Acquire.Client import ACLRule as _ACLRule

        if aclrule is None:
            aclrule = _ACLRule.reader()
        elif not isinstance(aclrule, _ACLRule):
            raise TypeError("The aclrule must be type ACLRule")

        if expires_datetime is None:
            from Acquire.ObjectStore import get_datetime_future \
                as _get_datetime_future
            expires_datetime = _get_datetime_future(days=1)
        else:
            from Acquire.ObjectStore import datetime_to_datetime \
                as _datetime_to_datetime
            expires_datetime = _datetime_to_datetime(expires_datetime)

        from Acquire.Client import PublicKey as _PublicKey
        from Acquire.Client import PrivateKey as _PrivateKey
        self._privkey = None

        if encrypt_key is None:
            self._privkey = _PrivateKey()
            encrypt_key = self._privkey.public_key()
        elif isinstance(encrypt_key, _PrivateKey):
            self._privkey = encrypt_key
            encrypt_key = encrypt_key.public_key()
        elif not isinstance(encrypt_key, _PublicKey):
            raise TypeError("The passed encryption key must be type PublicKey")

        self._expires_datetime = expires_datetime
        self._aclrule = aclrule
        self._uid = None

        from Acquire.Client import Authorisation as _Authorisation
        auth = _Authorisation(user=user,
                              resource="create_par %s" % self.fingerprint())

        args = {"authorisation": auth.to_data(),
                "par": self.to_data(),
                "encrypt_key": encrypt_key.to_data()}

        service = identifier.storage_service()

        result = service.call_function(function="create_filepar",
                                       args=args)

        # this UID should have the form {type}://{storage_uid}/{par_uid}
        # (although it may be encrypted)
        self._uid = result["par_uid"]

    def is_null(self):
        """Return whether or not this is null"""
        return self._identifier is None

    def is_authorised(self):
        """Return whether or not this has been authorised"""
        return self._uid is not None

    def fingerprint(self):
        """Return a fingerprint that can be used to show that
           the user authorised the request to create this PAR
        """
        if self.is_null():
            return None
        else:
            from Acquire.ObjectStore import datetime_to_string \
                as _datetime_to_string
            return "%s:%s:%s" % (self._identifier.fingerprint(),
                                 self._aclrule.fingerprint(),
                                 _datetime_to_string(self._expires_datetime))

    def service(self):
        """Return the service that authorised this PAR"""
        if self.is_null():
            return None
        else:
            return self._identifier.service()

    def service_url(self):
        """Return the URL of the service that authorised this PAR"""
        if self.is_null():
            return None
        else:
            return self._identifier.service_url()

    def service_uid(self):
        """Return the UID of the service that authorised this PAR"""
        if self.is_null():
            return None
        else:
            return self._identifier.service_uid()

    def resolve(self, key=None):
        """Resolve this PAR into the authorised Drive or File object, ready
           for download, upload etc.

           If this is an encrypted PAR, then you will need to pass
           in the valid decryption key to gain access
        """
        from Acquire.Client import Drive as _Drive
        return _Drive()

    def expires_when(self):
        """Return when this PAR expires (or expired)"""
        if not self.is_authorised():
            return None
        else:
            return self._expires_datetime

    def seconds_remaining(self, buffer=30):
        """Return the number of seconds remaining before this PAR expires.
           This will return 0 if the PAR has already expired. To be safe,
           you should renew PARs if the number of seconds remaining is less
           than 60. This will subtract 'buffer' seconds from the actual
           validity to provide a buffer against race conditions (function
           says this is valid when it is not)

           Args:
                buffer (int, default=30): buffer PAR validity (seconds)
           Returns:
                datetime: Seconds remaining on PAR validity
        """
        if not self.is_authorised():
            return 0

        from Acquire.ObjectStore import get_datetime_now as _get_datetime_now

        buffer = float(buffer)

        if buffer < 0:
            buffer = 0

        now = _get_datetime_now()

        delta = (self._expires_datetime - now).total_seconds() - buffer

        if delta < 0:
            return 0
        else:
            return delta

    def to_data(self):
        """Return a json-serialisable dictionary of this FilePAR"""
        if self.is_null():
            return None

        from Acquire.ObjectStore import datetime_to_string \
            as _datetime_to_string

        data = {}

        data["identifier"] = self._identifier.to_data()
        data["aclrule"] = self._aclrule.to_data()
        data["expires_datetime"] = _datetime_to_string(self._expires_datetime)
        data["uid"] = self._uid

        return data

    @staticmethod
    def from_data(data):
        """Return a FilePAR constructed from the json-deserialised passed
           dictionary
        """
        if data is None or len(data) == 0:
            return FilePAR()

        f = FilePAR()

        from Acquire.Client import Identifier as _Identifier
        from Acquire.Client import ACLRule as _ACLRule
        from Acquire.ObjectStore import string_to_datetime \
            as _string_to_datetime

        f._identifier = _Identifier.from_data(data["identifier"])
        f._aclrule = _ACLRule.from_data(data["aclrule"])
        f._expires_datetime = _string_to_datetime(data["expires_datetime"])
        f._uid = data["uid"]

        return f
