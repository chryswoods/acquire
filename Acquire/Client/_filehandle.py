
__all__ = ["FileHandle"]


class FileHandle:
    """This class holds all of the information about a file that is
       held in a Drive, including its size
       and checksum, and information about previous versions. It
       provides a handle that you can use to download or delete
       the file, to upload new versions, or to move the data between
       hot and cold storage or pay for extended storage
    """
    def __init__(self, filename=None):
        """Construct a handle for the local file 'filename'. This will
           create the initial version of the file that can be uploaded
           to the storage service
        """
        if filename is not None:
            from Acquire.Access import get_filesize_and_checksum \
                as _get_filesize_and_checksum

            self._filename = str(filename)
            (filesize, cksum) = _get_filesize_and_checksum(filename=filename)

            self._filesize = filesize
            self._checksum = cksum

            from Acquire.Storage import ACLRule as _ACLRule
            self._acl = _ACLRule.owner()
            self._version = None
        else:
            self._filename = None

    def is_null(self):
        """Return whether or not this this null"""
        return self._filename is None

    def filename(self):
        """Return the object-store filename for this file"""
        return self._filename

    def filesize(self):
        """Return the size (in bytes) of this file"""
        if self.is_null():
            return 0
        else:
            return self._filesize

    def checksum(self):
        """Return the checksum of the contents of this file"""
        if self.is_null():
            return None
        else:
            return self._checksum

    def acl(self):
        """Return the ACL rule for the current user for this file"""
        return self._acl

    def version(self):
        """Return the version of this file on the storage service. This
           is a datetime of the upload of this version. You will need to
           query the storage service to find if there are other versions.
           This returns None if this file has not yet been uploaded
        """
        if self.is_null():
            return None
        else:
            return self._version

    def fingerprint(self):
        """Return a fingerprint for this file"""
        return "%s-%s-%s" % (self.filename(), self.filesize(), self.checksum())

    def add_old_versions(self, old_fileinfo):
        """Record an old version of this file described in the passed
           'old_fileinfo'
        """
        if self.is_null() or old_fileinfo.is_null():
            return

        # somehow match filenames and acls... (should inherit ACLS?)

        # add the versions to our dictionary

    def to_data(self):
        """Return a json-serialisable dictionary for this object"""
        data = {}

        if not self.is_null():
            from Acquire.ObjectStore import datetime_to_string \
                as _datetime_to_string
            data["filename"] = self.filename()
            data["filesize"] = self.filesize()
            data["checksum"] = self.checksum()
            data["acl"] = self.acl().to_data()
            data["version"] = _datetime_to_string(self.version())

        return data

    @staticmethod
    def from_data(data):
        """Return an object created from the passed json-deserialised
           dictionary
        """
        f = FileHandle()

        if data is not None and len(data) > 0:
            from Acquire.Storage import ACLRule as _ACLRule
            from Acquire.ObjectStore import string_to_datetime \
                as _string_to_datetime

            f._filename = data["filename"]
            f._filesize = int(data["filesize"])
            f._checksum = data["checksum"]
            f._acl = _ACLRule.from_data(data["acl"])
            f._version = _string_to_datetime(data["version"])

        return f
