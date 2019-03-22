
__all__ = ["DriveMeta"]


class DriveMeta:
    """This is a lightweight class that holds the metadata about
       a Drive
    """
    def __init__(self, name=None, uid=None, container=None):
        """Construct a drive with a specified name and (optionally) UID.
           'container' is the UID of the drive that contains this drive,
           at least for the user who has accessed this drive via a path.
           If 'container' is none, then the user is accessing this
           drive as a top-level drive
        """
        self._name = name
        self._uid = uid
        self._container = container

    def __str__(self):
        """Return a string representation"""
        if self.is_null():
            return "DriveMeta::null"
        else:
            return "DriveMeta(%s)" % self._name

    def __repr__(self):
        return self.__str__()

    def is_null(self):
        """Return whether or not this is null"""
        return self._name is None

    def name(self):
        """Return the name of the drive"""
        return self._name

    def uid(self):
        """If known, return the UID of the drive"""
        return self._uid

    def is_top_level(self):
        """Return whether or not this drive was accessed as a
           top-level drive
        """
        return self._container is None

    def container_uid(self):
        """Return the UID of the drive that contains this drive, at
           least via the access path followed by the user.
           This returns None if the user accessed this drive as
           a top-level drive
        """
        return self._container

    def to_data(self):
        """Return a json-serialisable dictionary of this object"""
        data = {}

        if not self.is_null():
            data["name"] = str(self._name)

            if self._uid is not None:
                data["uid"] = str(self._uid)

            if self._container is not None:
                data["container"] = str(self._container)

        return data

    @staticmethod
    def from_data(data):
        """Return an object constructed from the passed json-deserialised
           dictionary
        """

        d = DriveMeta()

        if data is not None and len(data) > 0:
            d._name = data["name"]

            if "uid" in data:
                d._uid = data["uid"]

            if "container" in data:
                d._container = data["container"]

        return d
