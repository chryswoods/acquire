
__all__ = ["FileHandle"]


class FileHandle:
    """This class holds all of the information about a file that is
       held in a Drive, including its size
       and checksum, and information about previous versions. It
       provides a handle that you can use to download or delete
       the file, to upload new versions, or to move the data between
       hot and cold storage or pay for extended storage
    """
    def __init__(self, filename=None, remote_filename=None,
                 aclrule=None, fileinfo=None):
        """Construct a handle for the local file 'filename'. This will
           create the initial version of the file that can be uploaded
           to the storage service
        """
        if filename is not None:
            from Acquire.Access import get_filesize_and_checksum \
                as _get_filesize_and_checksum

            (filesize, cksum) = _get_filesize_and_checksum(filename=filename)

            self._filename = filename

            if remote_filename is None:
                import os as _os
                self._remote_filename = _os.path.split(self._filename)[1]
            else:
                self._remote_filename = str(remote_filename)

            from Acquire.Storage import ACLRule as _ACLRule
            if aclrule is not None:
                if not isinstance(aclrule, _ACLRule):
                    raise TypeError("The ACL rules must be type ACLRule")

                self._aclrule = aclrule
            else:
                self._aclrule = _ACLRule.inherit()

            self._filesize = filesize
            self._checksum = cksum
        elif fileinfo is not None:
            # construct as a handle to a remote file
            from Acquire.Storage import FileInfo as _FileInfo
            if not isinstance(fileinfo, _FileInfo):
                raise TypeError("The fileinfo must be type FileInfo")

            self._filename = fileinfo.filename()
            self._remote_filename = fileinfo.filename()
            self._aclrule = fileinfo.acl()

            self._filesize = fileinfo.filesize()
            self._checksum = fileinfo.checksum()
        else:
            self._filename = None

    def __str__(self):
        """Return a string representation of the file"""
        if self.is_null():
            return "FileHandle::null"

        return "FileHandle(filename='%s', acl=%s)" % \
            (self.filename(), self.acl())

    def is_null(self):
        """Return whether or not this this null"""
        return self._filename is None

    def acl(self):
        """Return the ACL rule for this file"""
        return self._aclrule

    def filename(self):
        """Return the local filename for this file"""
        return self._filename

    def remote_filename(self):
        """Return the remote (object store) filename for this file"""
        return self._remote_filename

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

    def fingerprint(self):
        """Return a fingerprint for this file"""
        return "%s:%s:%s:%s" % (self.filename(), self.remote_filename(),
                                self.filesize(), self.checksum())

    def to_data(self):
        """Return a json-serialisable dictionary for this object"""
        data = {}

        if not self.is_null():
            from Acquire.ObjectStore import datetime_to_string \
                as _datetime_to_string
            data["filename"] = self.filename()
            data["remote_filename"] = self.remote_filename()
            data["filesize"] = self.filesize()
            data["checksum"] = self.checksum()
            data["aclrule"] = self.acl().to_data()

        return data

    @staticmethod
    def from_data(data):
        """Return an object created from the passed json-deserialised
           dictionary
        """
        f = FileHandle()

        if data is not None and len(data) > 0:
            from Acquire.Storage import ACLRule as _ACLRule
            f._filename = data["filename"]
            f._remote_filename = data["remote_filename"]
            f._filesize = int(data["filesize"])
            f._checksum = data["checksum"]
            f._aclrule = _ACLRule.from_data(data["aclrule"])

        return f
