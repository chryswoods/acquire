
__all__ = ["DriveInfo"]

_drive_root = "storage/drive"


class DriveInfo:
    """This class provides a service-side handle to the information
       about a particular cloud drive
    """
    def __init__(self, drive_uid=None, user_guid=None,
                 is_authorised=False):
        """Construct a DriveInfo for the drive with UID 'drive_uid',
           and optionally the GUID of the user making the request
           (and whether this was authorised)
        """
        self._drive_uid = drive_uid
        self._user_guid = user_guid
        self._is_authorised = is_authorised

        if self._drive_uid is not None:
            self.load()

    def is_null(self):
        return self._drive_uid is None

    def _drive_key(self):
        """Return the key for this drive in the object store"""
        return "%s/%s/info" % (_drive_root, self._drive_uid)

    def is_opened_by_owner(self):
        """Return whether or not this drive was opened and authorised
           by one of the drive owners
        """
        if self._user_guid is None or (not self._is_authorised):
            return False

        try:
            return self._acls[self._user_guid].is_owner()
        except:
            return False

    def num_owners(self):
        """Return the number of users who have ownership permissions
           for this drive
        """
        n = 0
        for acl in self._acls.values():
            n += acl.is_owner()

        return n

    def num_readers(self):
        """Return the number of users who have read permissions
           for this drive
        """
        n = 0
        for acl in self._acls.values():
            n += acl.is_readable()

        return n

    def num_writers(self):
        """Return the number of users who have write permissions
           for this drive
        """
        n = 0
        for acl in self._acls.values():
            n += acl.is_writeable()

        return n

    def set_permission(self, user_guid, aclrule):
        """Set the permission for the user with the passed user_guid
           to 'aclrule". Note that you can only do this if you are the
           owner and this drive was opened in an authorised way. Also
           note that you cannot remove your own ownership permission
           if this would leave the drive without any owners
        """
        if self.is_null():
            return

        from Acquire.Storage import ACLRule as _ACLRule
        if not isinstance(aclrule, _ACLRule):
            raise TypeError("The aclrule must be type ACLRule")

        # make sure we have the latest version
        self.load()

        if not self.is_opened_by_owner():
            raise PermissionError(
                "You cannot change user permissions as you are either "
                "not the owner of this drive or you failed to provide "
                "authorisation when you opened the drive")

        try:
            old_acl = self._acls[user_guid]
        except:
            old_acl = _ACLRule()

        if self.num_owners() == 1 and old_acl.is_owner():
            raise PermissionError(
                "You cannot remove ownership permissions from the only "
                "owner of the drive")

        if aclrule.is_null():
            del self._acls[user_guid]
        else:
            self._acls[user_guid] = aclrule

        self.save()
        self.load()

        if self.num_owners() == 0:
            # race-condition of two people removing their ownership
            # at the same time - restore old permissions and raise an
            # error
            self._acls[user_guid] = old_acl
            self.save()
            self.load()
            raise PermissionError(
                "You cannot stop yourself being an owner as this would "
                "leave the drive with no owners!")

    def load(self):
        """Load the metadata about this drive from the object store"""
        if self.is_null():
            return

        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        bucket = _get_service_account_bucket()

        drive_key = self._drive_key()

        try:
            data = _ObjectStore.get_object_from_json(bucket, drive_key)
        except:
            data = None

        if data is None:
            if self._user_guid is None:
                # we cannot create the drive as we don't know who
                # requested it
                raise PermissionError(
                    "Cannot create the DriveInfo for a new drive as the "
                    "original request did not specify the creating user")
            elif not self._is_authorised:
                # we cannot create the drive if the request was not
                # authorised
                raise PermissionError(
                    "Cannot create the DriveInfo for a new drive as the "
                    "original request was not authorised by the user")

            # create a new drive and save it...
            from Acquire.Storage import ACLRule as _ACLRule

            self._acls = {self._user_guid: _ACLRule.owner()}
            data = self.to_data()

            data = _ObjectStore.set_ins_object_from_json(bucket, drive_key,
                                                         data)

        from copy import copy as _copy
        other = DriveInfo.from_data(data)

        user_guid = self._user_guid
        is_authorised = self._is_authorised

        self.__dict__ = _copy(other.__dict__)

        self._user_guid = user_guid
        self._is_authorised = is_authorised

    def save(self):
        """Save the metadata about this drive to the object store"""
        if self.is_null():
            return

        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        bucket = _get_service_account_bucket()

        drive_key = self._drive_key()

        data = self.to_data()
        _ObjectStore.set_object_from_json(bucket, drive_key, data)

    def to_data(self):
        """Return a json-serialisable dictionary for this object"""
        data = {}

        if not self.is_null():
            from Acquire.ObjectStore import dict_to_string as _dict_to_string
            data["uid"] = self._drive_uid
            data["acls"] = _dict_to_string(self._acls)

        return data

    @staticmethod
    def from_data(data):
        """Return a DriveInfo constructed from the passed json-deserialised
           dictionary
        """
        info = DriveInfo()

        if data is None or len(data) == 0:
            return info

        from Acquire.Storage import ACLRule as _ACLRule
        from Acquire.ObjectStore import string_to_dict as _string_to_dict

        info._acls = _string_to_dict(data["acls"], _ACLRule)
        info._drive_uid = str(data["uid"])

        return info
