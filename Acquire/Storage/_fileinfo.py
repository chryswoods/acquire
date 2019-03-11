
__all__ = ["FileInfo", "VersionInfo"]


class VersionInfo:
    """This class holds specific info about a version of a file"""
    def __init__(self, filesize=None, checksum=None):
        """Construct the version of the file that has the passed
           size and checksum
        """
        if filesize is not None:
            from Acquire.ObjectStore import create_uuid as _create_uuid
            self._filesize = filesize
            self._checksum = checksum
            self._file_uid = _create_uuid()
        else:
            self._filesize = None

    def is_null(self):
        """Return whether or not this is null"""
        return self._filesize is None

    def filesize(self):
        """Return the size in bytes of this version of the file"""
        if self.is_null():
            return 0
        else:
            return self._filesize

    def checksum(self):
        """Return the checksum for this version of the file"""
        if self.is_null():
            return None
        else:
            return self._checksum

    def uid(self):
        """Return the UID of this version of the file in object store"""
        if self.is_null():
            return None
        else:
            return self._file_uid

    def to_data(self):
        """Return a json-serialisable dictionary for this object"""
        data = {}

        if not self.is_null():
            data["filesize"] = self.filesize()
            data["checksum"] = self.checksum()
            data["uid"] = self.uid()

        return data

    @staticmethod
    def from_data(data):
        """Return this object constructed from the passed json-deserialised
           dictionary
        """
        v = VersionInfo()

        if data is not None and len(data) > 0:
            v._filesize = data["filesize"]
            v._checksum = data["checksum"]
            v._uid = data["uid"]

        return v


class FileInfo:
    """This class provides information about a user-file that has
       been uploaded to the storage service. This includes all
       versions of the file, the ACLs for different users etc.

       Just as Acquire.Client.Drive provides the client-side view
       of Acquire.Storage.DriveInfo, so to does
       Acquire.Client.FileHandle provide the client-side view
       of Acquire.Storage.FileInfo
    """
    def __init__(self, filehandle=None, user_guid=None):
        """Construct from a passed filehandle of a file that will be
           uploaded
        """
        self._filename = None

        if filehandle is not None:
            from Acquire.Client import FileHandle as _FileHandle

            if not isinstance(filehandle, _FileHandle):
                raise TypeError(
                    "The filehandle must be of type FileHandle")

            if filehandle.is_null():
                return

            from Acquire.ObjectStore import get_datetime_now \
                as _get_datetime_now

            self._filename = filehandle.filename()

            version = VersionInfo(filesize=filehandle.filesize(),
                                  checksum=filehandle.checksum())

            self._versions = {_get_datetime_now(): version}
            self._acls = {user_guid: filehandle.acl()}

    def is_null(self):
        """Return whether or not this is null"""
        return self._filename is None

    def filename(self):
        """Return the object-store filename for this file"""
        return self._filename

    def _version_info(self, version=None):
        """Return the version info object of the latest version of
           the file, or the passed version
        """
        if self.is_null():
            return VersionInfo()
        else:
            if version is None:
                version = self._latest_version

            try:
                return self._versions[version]
            except:
                from Acquire.Storage import VersionNotFoundError
                raise VersionNotFoundError(
                    "Cannot find the version '%s' for file '%s'" %
                    (version, self.filename()))

    def filesize(self, version=None):
        """Return the size (in bytes) of the latest (or specified)
           version of this file"""
        return self._version_info(version).filesize()

    def checksum(self, version=None):
        """Return the checksum of the latest (or specified) version
           of this file
        """
        return self._version_info(version).checksum()

    def file_uid(self, version=None):
        """Return the UID of the latest (or specified) version
           of this file
        """
        return self._version_info(version).uid()

    def acl(self, user_guid=None):
        """Return the ACL rule for the specified user, or if that is not
           specified, the ACL mask that will be applied to the ACL
           for the drive
        """
        try:
            return self._acls[user_guid]
        except:
            from Acquire.Storage import ACLRule as _ACLRule
            return _ACLRule.null()

    def latest_version(self):
        """Return the latest version of this file on the storage service. This
           is a datetime of the upload of the latest version. You will need to
           use the 'versions' function to find if there are other versions.
        """
        if self.is_null():
            return None
        else:
            return self._latest_version

    def versions(self):
        """Return the sorted list of all versions of this file on the
           storage service
        """
        v = list(self._versions.keys())
        v.sort()
        return v

    def to_data(self):
        """Return a json-serialisable dictionary for this object"""
        data = {}

        if not self.is_null():
            from Acquire.ObjectStore import datetime_to_string \
                as _datetime_to_string

            data["filename"] = self.filename()

            versions = []

            for version, info in self._versions.items():
                versions.append((_datetime_to_string(version), info.to_data()))

            acls = []

            for user_guid, acl in self._acls.items():
                acls.append((user_guid, acl.to_data()))

            data["versions"] = versions
            data["acls"] = acls

        return data

    @staticmethod
    def from_data(data):
        """Return this object constructed from the passed json-deserialised
           dictionary
        """
        f = FileInfo()

        if data is not None and len(data) > 0:
            from Acquire.ObjectStore import string_to_datetime \
                as _string_to_datetime
            from Acquire.Storage import ACLRule as _ACLRule

            f._filename = data["filename"]

            versions = {}

            for version, info in data["versions"]:
                versions[_string_to_datetime(version)] = \
                    VersionInfo.from_data(info)

            acls = {}

            for user_guid, acl in data["acls"]:
                acls[user_guid] = _ACLRule.from_data(acl)

            f._versions = versions
            f._acls = acls

            f._latest_version = f.versions()[-1]

        return f
