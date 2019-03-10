
__all__ = ["Drive", "get_drive", "get_drives"]


def _get_storage_url():
    """Function to discover and return the default storage url"""
    return "http://fn.acquire-aaai.com:8080/t/storage"


def _get_storage_service(storage_url=None):
    """Function to return the storage service for the system"""
    if storage_url is None:
        storage_url = _get_storage_url()

    from Acquire.Client import Service as _Service
    service = _Service(storage_url)

    if not service.is_storage_service():
        from Acquire.Client import LoginError
        raise LoginError(
            "You can only use a valid storage service to get CloudDrive info! "
            "The service at '%s' is a '%s'" %
            (storage_url, service.service_type()))

    if service.service_url() != storage_url:
        service.update_service_url(storage_url)

    return service


def _create_drive(user, name, driveinfo, storage_service):
    """Internal function used to create a Drive"""
    from Acquire.Client import ACLRule as _ACLRule
    drive = Drive()
    drive._name = name
    drive._user = user
    drive._drive_uid = driveinfo["drive_uid"]
    drive._acl = _ACLRule.from_data(driveinfo["acl"])
    drive._storage_service = storage_service
    return drive


def get_drive(user, name=None, storage_service=None, storage_url=None,
              autocreate=True):
    """Return the drive called 'name' of the passed user. Note that the
       user must be authenticated to call this function. The name
       will default to 'main' if it is not set, and the drive will
       be created automatically is 'autocreate' is True and the
       drive does not exist
    """
    if storage_service is None:
        storage_service = _get_storage_service(storage_url)
    else:
        if not storage_service.is_storage_service():
            raise TypeError("You can only query drives using "
                            "a valid storage service")

    if name is None:
        name = "main"
    else:
        name = str(name)

    if autocreate:
        autocreate = True
    else:
        autocreate = False

    from Acquire.Client import Authorisation as _Authorisation
    authorisation = _Authorisation(resource="UserDrives", user=user)

    args = {"authorisation": authorisation.to_data(),
            "name": name, "autocreate": autocreate}

    response = storage_service.call_function(function="open_drive", args=args)

    return _create_drive(user=user, name=name, storage_service=storage_service,
                         driveinfo=response["drives"][name])


def get_drives(user, storage_service=None, storage_url=None):
    """Return all of the drives of the passed user. Note that the
       user must be authenticated to call this function
    """
    if storage_service is None:
        storage_service = _get_storage_service(storage_url)
    else:
        if not storage_service.is_storage_service():
            raise TypeError("You can only query drives using "
                            "a valid storage service")

    from Acquire.Client import Authorisation as _Authorisation
    authorisation = _Authorisation(resource="UserDrives", user=user)

    args = {"authorisation": authorisation.to_data()}

    response = storage_service.call_function(function="open_drive", args=args)

    drives = {}
    for name, value in response["drives"].items():
        drives[name] = _create_drive(user=user, name=name,
                                     storage_service=storage_service,
                                     driveinfo=value)

    return drives


class Drive:
    """This class provides a handle to a user's drive (space
       to hold files and folders). A drive is associated with
       a single storage service and can be shared amongst several
       users. Each drive has a unique UID, with users assiging
       their own shorthand names.
    """
    def __init__(self, user=None, name=None, storage_service=None,
                 storage_url=None, autocreate=True):
        """Construct a handle to the drive that the passed user
           calls 'name' on the passed storage service. If
           'autocreate' is True and the user is logged in then
           this will automatically create the drive if
           it doesn't exist already
        """
        if user is not None:
            drive = get_drive(user=user, name=name,
                              storage_service=storage_service,
                              storage_url=storage_url, autocreate=autocreate)

            from copy import copy as _copy
            self.__dict__ = _copy(drive.__dict__)
        else:
            self._drive_uid = None

    def __str__(self):
        if self.is_null():
            return "Drive::null"
        else:
            return "Drive(user='%s', name='%s')" % \
                    (self._user.username(), self.name())

    def is_null(self):
        """Return whether or not this drive is null"""
        return self._drive_uid is None

    def acl(self):
        """Return the access control list for the user on this drive"""
        if self.is_null():
            from Acquire.Client import ACLRule as _ACLRule
            return _ACLRule.null()
        else:
            return self._acl

    def name(self):
        """Return the name given to this drive by the user"""
        return self._name

    def uid(self):
        """Return the UID of this drive"""
        return self._drive_uid

    def guid(self):
        """Return the global UID of this drive (combination of the
           UID of the storage service and UID of the drive)
        """
        if self.is_null():
            return None
        else:
            return "%s@%s" % (self.storage_service().uid(), self.uid())

    def storage_service(self):
        """Return the storage service for this drive"""
        if self.is_null():
            return None
        else:
            return self._storage_service
