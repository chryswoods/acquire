

class Identifier:
    """This class holds a globally-resolvable identifier for a
       file or Drive. This can be used to refer to files or drives,
       as well as providing the functionality to download those
       files or drives to local storage
    """
    def __init__(self, drive_guid=None, filename=None, version=None):
        """Construct an Identifier. This uses the GUID of the
           drive to identify the drive, and then (optionally) the
           name of the file in the drive, and then the specific
           version.

           If the filename is not supplied, then this identifies
           the drive itself. If a version is not supplied, then this
           identifies the latest version of the file
        """
        self._drive_guid = drive_guid

        if self._drive_guid is not None:
            self._filename = filename
            self._version = version

            if self._filename is not None:
                from Acquire.ObjectStore import string_to_encoded \
                    as _string_to_encoded
                self._encoded_filename = _string_to_encoded(self._filename)
            else:
                self._encoded_filename = None

    def is_null(self):
        return self._drive_guid is None

    def __str__(self):
        if self.is_null():
            return "Identifier::null"
        else:
            return "%s:%s:%s" % (self._drive_guid, self._encoded_filename,
                                 self._version)

    def preauthorise(user):
        """Pre-authorise this request - this will allow anyone who
           receives this Identifier to resolve it and download
           the file
        """

    def resolve(self, user=None, download_to=None):
        """Resolve the identifier, downloading the file (or all files
           in the drive) to 'download_to' (or the current directory
           if this isn't specified).

           You need to supply a user so that we can check that you
           have permission to access this file/drive. If no user
           is supplied then you will only be able to access
           publicly visible files/drives.
        """
