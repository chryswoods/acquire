

__all__ = ["ACLRule"]


class ACLRule:
    """This class holds the access control list (ACL) rule for
       a particular user accessing a particular bucket
    """
    def __init__(self, is_owner=False, is_readable=False, is_writeable=False):
        """Construct a default rule. By default this rule has zero
           permissions (cannot own, read or write)
        """
        if is_owner:
            self._is_owner = True
        else:
            self._is_owner = False

        if is_readable:
            self._is_readable = True
        else:
            self._is_readable = False

        if is_writeable:
            self._is_writeable = True
        else:
            self._is_writeable = False

    def is_owner(self):
        """Return whether or not the user is the owner of the bucket"""
        return self._is_owner

    def is_readable(self):
        """Return whether or not the user can read this bucket"""
        return self._is_readable

    def is_writeable(self):
        """Return whether or not the user can write to this bucket"""
        return self._is_writeable

    def set_owner(self, is_owner=True):
        """Set the user as an owner of the bucket"""
        if is_owner:
            self._is_owner = True
        else:
            self._is_owner = False

    def set_readable(self, is_readable=True):
        """Set the readable rule to 'is_readable'"""
        if is_readable:
            self._is_readable = True
        else:
            self._is_readable = False

    def set_writeable(self, is_writeable=True):
        """Set the writeable rule to 'is_writeable'"""
        if is_writeable:
            self._is_writeable = True
        else:
            self._is_writeable = False

    def set_readable_writeable(self, is_readable_writeable=True):
        """Set both the readable and writeable rules to
           'is_readable_writeable'
        """
        if is_readable_writeable:
            self._is_readable = True
            self._is_writeable = True
        else:
            self._is_readable = False
            self._is_writeable = False

    def to_data(self):
        """Return this object converted to a json-serlisable dictionary"""
        data = {}
        data["is_owner"] = self._is_owner
        data["is_readable"] = self._is_readable
        data["is_writeable"] = self._is_writeable

    @staticmethod
    def from_data(data):
        """Return this object constructed from the passed json-deserialised
           dictionary
        """
        if data is None:
            return None

        rule = ACLRule()

        if "is_owner" in data:
            if data["is_owner"]:
                rule._is_owner = True

        if "is_readable" in data:
            if data["is_readable"]:
                rule._is_readable = True

        if "is_writeable" in data:
            if data["is_writeable"]:
                rule._is_writeable = True

        return rule
