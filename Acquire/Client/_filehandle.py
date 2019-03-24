
__all__ = ["FileHandle"]


_magic_dict = {
    b"\x1f\x8b\x08": "gz",
    b"\x42\x5a\x68": "bz2",
    b"\x50\x4b\x03\x04": "zip"
    }


_max_magic_len = max(len(x) for x in _magic_dict)


def _should_compress(filename, filesize):
    """Return whether or not the passed file is worth compressing.
       It is not worth compressing very small files (<128 bytes) or
       already-compressed files
    """
    if filesize < 128:
        return False

    with open(filename, "rb") as FILE:
        file_start = FILE.read(_max_magic_len)

    for magic in _magic_dict.keys():
        if file_start.startswith(magic):
            return False

    return True


def _bz2compress(inputfile, outputfile=None):
    """Compress 'inputfile', writing the output to 'outputfile'
       If 'outputfile' is None, then this will create a new filename
       in the current directory for the file. This returns
       the filename for the compressed file
    """
    import bz2 as _bz2
    IFILE = open(inputfile, "rb")

    if outputfile is None:
        import tempfile as _tempfile
        (tmpfile, outputfile) = _tempfile.mkstemp(dir=".")
        tmpfile.close()
        is_tempfile = True
    else:
        is_tempfile = False

    try:
        OFILE = _bz2.BZ2File(outputfile, "wb", compresslevel=9)

        # compress data in MB blocks
        data = IFILE.read(size=1048576)

        while data:
            OFILE.write(data)
            data = IFILE.read(size=1048576)

        IFILE.close()
        OFILE.close()

        return outputfile
    except:
        # make sure we delete the temporary file
        if is_tempfile:
            import os as _os
            _os.unlink(outputfile)

        raise


class FileHandle:
    """This class holds all of the information about a file that is
       held in a Drive, including its size
       and checksum, and information about previous versions. It
       provides a handle that you can use to download or delete
       the file, to upload new versions, or to move the data between
       hot and cold storage or pay for extended storage
    """
    def __init__(self, filename=None, remote_filename=None,
                 aclrule=None, drive_uid=None, filemeta=None, compress=True):
        """Construct a handle for the local file 'filename'. This will
           create the initial version of the file that can be uploaded
           to the storage service
        """
        self._local_filename = None
        self._local_filedata = None
        self._compression = None
        self._compressed_filename = None
        self._drive_uid = drive_uid

        if filename is not None:
            from Acquire.Access import get_filesize_and_checksum \
                as _get_filesize_and_checksum
            import os as _os

            (filesize, cksum) = _get_filesize_and_checksum(filename=filename)

            if compress and _should_compress(filename=filename,
                                             filesize=filesize):
                import bz2 as _bz2
                if filesize < 1048576:
                    # this is not big, so better to compress in memory
                    from Acquire.Access import get_size_and_checksum \
                        as _get_size_and_checksum
                    data = open(filename, "rb").read()
                    data = _bz2.compress(data)
                    (filesize, cksum) = _get_size_and_checksum(data=data)
                    self._local_filedata = data
                    self._compression = "bz2"
                else:
                    # this is a bigger file, so compress on disk
                    try:
                        self._compressed_filename = _bz2compress(
                                                        inputfile=filename)
                    except:
                        pass

                    if self._compressed_filename is not None:
                        self._compression = "bz2"
                        (filesize, cksum) = _get_filesize_and_checksum(
                                            filename=self._compressed_filename)
            elif filesize < 1048576:
                # this is small enough to hold in memory
                self._local_filedata = open(filename, "rb").read()

            if self._compressed_filename is None:
                self._local_filename = filename

            self._filesize = filesize
            self._checksum = cksum

            if remote_filename is None:
                self._filename = _os.path.split(filename)[1]
            else:
                self._filename = _os.path.split(remote_filename)[1]

            from Acquire.Storage import ACLRule as _ACLRule
            if aclrule is not None:
                if not isinstance(aclrule, _ACLRule):
                    raise TypeError("The ACL rules must be type ACLRule")

                self._aclrule = aclrule
            else:
                self._aclrule = _ACLRule.inherit()

        elif filemeta is not None:
            # construct as a handle to a remote file
            from Acquire.Client import FileMeta as _FileMeta
            if not isinstance(filemeta, _FileMeta):
                raise TypeError("The filemeta must be type FileMeta")

            self._filename = filemeta.filename()
            self._aclrule = filemeta.acl()
            self._compression = filemeta.compression()

            self._filesize = filemeta.filesize()
            self._checksum = filemeta.checksum()

            self._drive_uid = None
        else:
            self._filename = None

    def __del__(self):
        """Ensure we delete the temporary file before being destroyed"""
        if self._compressed_filename is not None:
            import os as _os
            _os.unlink(self._compressed_filename)

    def __str__(self):
        """Return a string representation of the file"""
        if self.is_null():
            return "FileHandle::null"

        return "FileHandle(filename='%s', acl=%s)" % \
            (self.filename(), self.acl())

    def is_null(self):
        """Return whether or not this this null"""
        return self._filename is None

    def is_compressed(self):
        """Return whether or not the file is compressed on transport"""
        return self._compression is not None

    def compression_type(self):
        """Return a string describing the compression scheme used by the
           filehandle when transporting the file, or None if the data
           is not compressed
        """
        return self._compression

    def is_localdata(self):
        """Return whether or not this file is so small that the data
           is held in memory
        """
        return self._local_filedata is not None

    def local_filedata(self, uncompress=False):
        """Return the filedata for this file, assuming it is sufficiently
           small to be read in this way. Returns 'None' if not...

           If 'uncompress' is true, then uncompress the data
           (if it is compressed) before returning
        """
        if uncompress and self.is_compressed():
            if self._local_filedata is not None:
                import bz2 as _bz2
                return _bz2.decompress(self._local_filedata)
            else:
                return None
        else:
            return self._local_filedata

    def local_filename(self):
        """Return the local filename for this file"""
        if self.is_localdata():
            return None
        elif self.is_compressed():
            return self._compressed_filename
        else:
            return self._local_filename

    def drive_uid(self):
        """Return the UID of the drive on which this file is located"""
        return self._drive_uid

    def acl(self):
        """Return the ACL rule for this file"""
        return self._aclrule

    def filename(self):
        """Return the remote (object store) filename for this file"""
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

    def fingerprint(self):
        """Return a fingerprint for this file"""
        return "%s:%s:%s" % (self.filename(),
                             self.filesize(), self.checksum())

    def to_data(self):
        """Return a json-serialisable dictionary for this object. Note
           that this does not contain any information about the local
           file itself - just the name it should be called on the
           object store and the size, checksum and acl. If the file
           (or compressed file) is sufficiently small then this
           will also contain the packed version of that file data
        """
        data = {}

        if not self.is_null():
            from Acquire.ObjectStore import datetime_to_string \
                as _datetime_to_string
            data["filename"] = self.filename()
            data["filesize"] = self.filesize()
            data["checksum"] = self.checksum()
            data["aclrule"] = self.acl().to_data()
            data["drive_uid"] = self.drive_uid()

            if self._local_filedata is not None:
                from Acquire.ObjectStore import bytes_to_string \
                    as _bytes_to_string
                data["filedata"] = _bytes_to_string(self._local_filedata)

            if self._compression is not None:
                data["compression"] = self._compression

        return data

    @staticmethod
    def from_data(data):
        """Return an object created from the passed json-deserialised
           dictionary. Note that this does not contain any information
           about the local file itself - just the name it should be
           called on the object store and the size, checksum and acl.
           If the file (or compressed file) is sufficiently small then this
           will also contain the packed version of that file data
        """
        f = FileHandle()

        if data is not None and len(data) > 0:
            from Acquire.Storage import ACLRule as _ACLRule
            f._filename = data["filename"]
            f._filesize = int(data["filesize"])
            f._checksum = data["checksum"]
            f._aclrule = _ACLRule.from_data(data["aclrule"])
            f._drive_uid = data["drive_uid"]

            if "compression" in data:
                f._compression = data["compression"]

            if "filedata" in data:
                from Acquire.ObjectStore import string_to_bytes \
                    as _string_to_bytes

                f._local_filedata = _string_to_bytes(data["filedata"])

        return f