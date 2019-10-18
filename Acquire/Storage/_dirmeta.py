
__all__ = ["DirMeta"]


class DirMeta:
    """This is a lightweight class that holds the metadata about
       a particular directory in a Drive. Note that directories
       are not versioned, and they do not contain any ACLs
       (the ACLs are attached to files or drives). Directories
       just provide a convenient way to group together a set
       of files in a Drive
    """
    def __init__(self, name=None):
        """Construct, specifying the name of the directory"""
        self._name = name
        self._drive_metadata = None
        self._creds = None

    def __str__(self):
        """Return a string representation"""
        if self.is_null():
            return "DirMeta::null"
        else:
            return "DirMeta(%s)" % self._name

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        """Comparison equals"""
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def open(self, creds=None):
        """Open and return the File associated with this metadata"""
        from Acquire.Client import Directory as _Directory
        return _Directory.open(metadata=self, creds=creds)

    def is_null(self):
        """Return whether or not this is null"""
        return self._name is None

    def _copy_credentials(self, other):
        """Copy the drive metadata and credentials from 'other' to self"""
        if not isinstance(other, DirMeta):
            raise TypeError("other should be a DirMeta")

        self._drive_metadata = other._drive_metadata
        self._creds = other._creds

    def _set_drive_metadata(self, metadata, creds=None):
        """Internal function called by "Drive" to store the metadata
           of the drive that contains the Directory described by this metadata
        """
        from Acquire.Client import DriveMeta as _DriveMeta
        if not isinstance(metadata, _DriveMeta):
            raise TypeError("The metadata must be type DriveMeta")

        if creds is None:
            creds = metadata._creds
        else:
            if creds is not metadata._creds:
                from copy import copy as _copy
                metadata = _copy(metadata)
                metadata._creds = creds

        self._drive_metadata = metadata
        self._creds = metadata._creds

    def location(self):
        """Return a global location for this directory. This is unique
           for this directory and can be used to locate this directory from
           any other service.
        """
        if self.is_null():
            return None
        elif self._drive_metadata is None:
            raise PermissionError(
                "Cannot generate the location as we don't know "
                "which drive this file has come from!")

        from Acquire.Client import Location as _Location
        return _Location(drive_guid=self._drive_metadata.guid(),
                         filename=self.name())

    def name(self):
        """Return the name of the directory"""
        return self._name

    def drive(self):
        """Return the metadata for the drive that contains this file"""
        if self.is_null():
            return None
        elif self._drive_metadata is None:
            raise PermissionError(
                "Cannot get the drive metadata as we don't know "
                "which drive this directory has come from!")
        else:
            from copy import copy as _copy
            return _copy(self._drive_metadata)

    def to_data(self):
        """Return a json-serialisable dictionary of this object"""
        data = {}

        if self.is_null():
            return data

        data["name"] = str(self._name)

        return data

    @staticmethod
    def from_data(data):
        """Return a new DirMeta constructed from the passed json-deserialised
           dictionary
        """
        d = DirMeta()

        if data is not None and len(data) > 0:
            d._name = data["name"]

        return d
