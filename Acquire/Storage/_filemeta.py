
__all__ = ["FileMeta"]


class FileMeta:
    """This is a lightweight class that holds the metadata about
       a particular version of a file
    """
    def __init__(self, filename=None, uid=None, filesize=None,
                 checksum=None, uploaded_by=None, uploaded_when=None,
                 compression=None, acls=None):
        """Construct, specifying the filename, and then optionally
           other useful data
        """
        self._filename = filename
        self._uid = uid
        self._filesize = filesize
        self._checksum = checksum
        self._user_guid = uploaded_by
        self._datetime = uploaded_when
        self._compression = compression

        if acls is not None:
            if not isinstance(acls, dict):
                raise TypeError("The passed ACLs must be in a dictionary!")

            from Acquire.Client import ACLRule as _ACLRule
            for value in acls.values():
                if not isinstance(value, _ACLRule):
                    raise TypeError("The passed ACL must be a ACLRule")

        self._acls = acls

    def __str__(self):
        """Return a string representation"""
        if self.is_null():
            return "FileMeta::null"
        else:
            return "FileMeta(%s)" % self._filename

    def __repr__(self):
        return self.__str__()

    def is_null(self):
        """Return whether or not this is null"""
        return self._filename is None

    def has_metadata(self):
        """Return whether or not this file includes all of the
           metadata. If not, then only the filename is available
        """
        return self._uid is not None

    def filename(self):
        """Return the name of the file"""
        return self._filename

    def uid(self):
        """Return the UID of the file in the system"""
        if self.is_null():
            return None
        else:
            return self._uid

    def filesize(self):
        """If known, return the size of the file"""
        if self.is_null():
            return None
        else:
            return self._filesize

    def checksum(self):
        """If known, return a checksum of the file"""
        if self.is_null():
            return None
        else:
            return self._checksum

    def is_compressed(self):
        """If known, return whether or not this file is stored and
           transmitted in a compressed state
        """
        if self.is_null():
            return False
        else:
            return self._compression is not None

    def compression_type(self):
        """Return the compression type for this file, if it is
           stored and transmitted in a compressed state
        """
        if self.is_null():
            return None
        else:
            return self._compression

    def uploaded_by(self):
        """If known, return the GUID of the user who uploaded
           this version of the file
        """
        if self.is_null():
            return None
        else:
            return self._user_guid

    def uploaded_when(self):
        """If known, return the datetime when this version of
           the file was uploaded
        """
        if self.is_null():
            return None
        else:
            return self._datetime

    def acl(self, user_guid):
        """If known, return the ACL for this version of the file for the user
           with passed GUID. This ACL will override any ACL inherited
           from the drive
        """
        if self.is_null():
            return None

        if self._acls is None:
            return None

        try:
            return self._acls[user_guid]
        except:
            from Acquire.Storage import ACLRule as _ACLRule
            return _ACLRule.inherit()

    def to_data(self):
        """Return a json-serialisable dictionary of this object"""
        data = {}

        if self.is_null():
            return data

        data["filename"] = str(self._filename)

        if self._uid is not None:
            data["uid"] = str(self._uid)

        if self._filesize is not None:
            data["filesize"] = self._filesize

        if self._checksum is not None:
            data["checksum"] = self._checksum

        if self._user_guid is not None:
            data["user_guid"] = self._user_guid

        if self._compression is not None:
            data["compression"] = self._compression

        if self._acls is not None:
            from Acquire.ObjectStore import dict_to_string \
                as _dict_to_string
            data["acls"] = _dict_to_string(self._acls)

        if self._datetime is not None:
            from Acquire.ObjectStore import datetime_to_string \
                as _datetime_to_string
            data["datetime"] = _datetime_to_string(self._datetime)

        return data

    @staticmethod
    def from_data(data):
        """Return a new FileMeta constructed from the passed json-deserialised
           dictionary
        """
        f = FileMeta()

        if data is not None and len(data) > 0:
            f._filename = data["filename"]

            if "uid" in data:
                f._uid = data["uid"]

            if "filesize" in data:
                f._filesize = data["filesize"]

            if "checksum" in data:
                f._checksum = data["checksum"]

            if "user_guid" in data:
                f._user_guid = data["user_guid"]

            if "datetime" in data:
                from Acquire.ObjectStore import string_to_datetime \
                    as _string_to_datetime
                f._datetime = _string_to_datetime(data["datetime"])

            if "compression" in data:
                f._compression = data["compression"]

            if "acls" in data:
                from Acquire.ObjectStore import string_to_dict \
                    as _string_to_dict
                from Acquire.Client import ACLRule as _ACLRule
                f._acls = _string_to_dict(data["acls"], _ACLRule)

        return f
