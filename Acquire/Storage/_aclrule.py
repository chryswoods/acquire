

__all__ = ["ACLRule"]


class ACLRule:
    """This class holds the access control list (ACL) rule for
       a particular user accessing a particular bucket
    """
    def __init__(self, is_owner=False, is_readable=False, is_writeable=False):
        """Construct a default rule. By default this rule has zero
           permissions (cannot own, read or write)
        """
        if is_owner is None:
            self._is_owner = None
        elif is_owner:
            self._is_owner = True
        else:
            self._is_owner = False

        if is_readable is None:
            self._is_readable = None
        elif is_readable:
            self._is_readable = True
        else:
            self._is_readable = False

        if is_writeable is None:
            self._is_writeable = None
        elif is_writeable:
            self._is_writeable = True
        else:
            self._is_writeable = False

    def __str__(self):
        s = []

        if self.is_owner():
            s.append("owner")
        elif self.inherits_owner():
            s.append("inherits_owner")

        if self.is_writeable():
            s.append("writeable")
        elif self.inherits_writeable():
            s.append("inherits_writeable")

        if self.is_readable():
            s.append("readable")
        elif self.inherits_readable():
            s.append("inherits_readable")

        if len(s) == 0:
            return "ACLRule(no permission)"
        else:
            return "ACLRule(%s)" % ", ".join(s)

    @staticmethod
    def owner():
        """Return the ACLRule of an owner"""
        return ACLRule(is_owner=True, is_readable=True, is_writeable=True)

    @staticmethod
    def writer():
        """Return the ACLRule of a writer"""
        return ACLRule(is_owner=False, is_readable=True, is_writeable=True)

    @staticmethod
    def reader():
        """Return the ACLRule of a reader"""
        return ACLRule(is_owner=False, is_readable=True, is_writeable=False)

    @staticmethod
    def null():
        """Return a null (no-permission) rule"""
        return ACLRule(is_owner=False, is_readable=False, is_writeable=False)

    @staticmethod
    def inherit():
        """Return the ACL rule that means 'inherit permissions from parent'"""
        return ACLRule(is_owner=None, is_readable=None, is_writeable=None)

    def is_null(self):
        """Return whether or not this is null"""
        return self._is_owner is False and self._is_readable is False and \
            self._is_writeable is False

    def is_owner(self):
        """Return whether or not the user is the owner of the bucket"""
        return self._is_owner

    def is_readable(self):
        """Return whether or not the user can read this bucket"""
        return self._is_readable

    def is_writeable(self):
        """Return whether or not the user can write to this bucket"""
        return self._is_writeable

    def inherits_owner(self):
        """Return whether or not this inherits the owner status from parent"""
        return self._is_owner is None

    def inherits_readable(self):
        """Return whether or not this inherits the reader status
           from parent
        """
        return self._is_readable is None

    def inherits_writeable(self):
        """Return whether or not this inherits the writeable status
           from parent
        """
        return self._is_writeable is None

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

    def set_inherits_owner(self):
        """Set that this ACL inherits ownership from its parent"""
        self._is_owner = None

    def set_inherits_readable(self):
        """Set that this ACL inherits readable from its parent"""
        self._is_readable = None

    def set_inherits_writeable(self):
        """Set that this ACL inherits writeable from its parent"""
        self._is_writeable = None

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
        return data

    @staticmethod
    def from_data(data):
        """Return this object constructed from the passed json-deserialised
           dictionary
        """
        if data is None:
            return None

        is_owner = None
        is_readable = None
        is_writeable = None

        if "is_owner" in data:
            if data["is_owner"]:
                is_owner = True
            elif data["is_owner"] is not None:
                is_owner = False

        if "is_readable" in data:
            if data["is_readable"]:
                is_readable = True
            elif data["is_readable"] is not None:
                is_readable = False

        if "is_writeable" in data:
            if data["is_writeable"]:
                is_writeable = True
            elif data["is_writeable"] is not None:
                is_writeable = False

        return ACLRule(is_owner=is_owner,
                       is_writeable=is_writeable,
                       is_readable=is_readable)
