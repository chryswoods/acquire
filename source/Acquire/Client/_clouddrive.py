
from Acquire.Crypto import PrivateKey as _PrivateKey

from Acquire.Service import call_function as _call_function
from Acquire.Service import Service as _Service

from ._user import User as _User
from ._account import Account as _Account

from ._errors import LoginError

__all__ = ["CloudDrive"]


def _get_access_url():
    """Function to discover and return the default access service url"""
    return "http://130.61.60.88:8080/t/access"


def _get_access_service(access_url=None):
    """Function to return the access service for the system"""
    if access_url is None:
        access_url = _get_access_url()

    privkey = _get_private_key("function")
    response = _call_function(access_url, response_key=privkey)

    try:
        service = _Service.from_data(response["service_info"])
    except:
        raise LoginError("Have not received the access service info from "
                         "the access service at '%s' - got '%s'" %
                         (access_url, response))

    if not service.is_access_service():
        raise LoginError(
            "You can only use a valid access service to access resources! "
            "The service at '%s' is a '%s'" %
            (access_url, service.service_type()))

    if service.service_url() != access_url:
        service.update_service_url(access_url)

    return service


class CloudDrive:
    """This class represents a cloud drive. This provides a storage space
       to read and write files, and also to stream files as they are
       being written
    """
    def __init__(self, user, root=None, access_url=None):
        """Create a drive that is billed to the passed account and accessed
           via the passed access service. If 'root' is specified, then
           only read or write to the drive from 'root', otherwise allow
           reading/writing to all parts of the drive.
        """
        if not isinstance(user, _User):
            raise TypeError("The user must be of type User")

        if not user.is_logged_in():
            raise PermissionError(
                "You cannot create/access a cloud drive belonging to '%s' "
                "without that user being logged in" % str(user))

        self._user = user
        self._access_service = _get_access_service(access_url)

        if root:
            self._root = str(root)
        else:
            self._root = None

    def upload(self, source, destination=None, ignore_hidden=True,
               account=None):
        """Upload a file (or files) from 'source' to 'destination'. If
           'destination is not supplied, then the file(s) will be uploaded
           with 'destination' equals 'source' (i.e. they will have the same
           name on the cloud drive as they do on the drive). If 'destination'
           is supplied then if it ends in a "/" then the destination will
           be treated like a directory. If the number of source files is
           greater than 1 and only a single destination directory is provided
           then all files will be uploaded into that directory.

           If 'ignore_hidden' is true, then hidden files will be ignored
           when uploading directories (but not when specifying files
           manually)

           If you pass in 'account', then
           this account will be used to pay for the storage. The account
           can be authorised from a different user to the owner of the drive,
           although both the user and account must be in the logged-in state.

           If you don't specify the account then the default account for
           the user will be used.

           Note that you cannot overwrite a file that already exists. It has
           to be explicitly removed first.

           Note that this is an atomic function - either all of none
           of the files will be written.

           This will return the list of read-only handles to allow you
           (or anyone else) to read these files.
        """

        if source is None:
            return

        if account is None:
            if not self._user.is_logged_in():
                raise PermissionError(
                    "You cannot upload files unless you have logged into "
                    "your account. Please log in and try again.")

            account = _Account(user=self._user)

        from Acquire.Access import FileWriteRequest as _FileWriteRequest

        request = _FileWriteRequest(source=source, destination=destination,
                                    ignore_hidden=ignore_hidden,
                                    account=account)

        args = {"request": request.to_data()}

        privkey = _get_private_key("function")

        result = _call_function(
                    self._access_service.service_url(), "request",
                    args=args,
                    args_key=self._access_service.public_key(),
                    response_key=privkey,
                    public_cert=self._access_service.public_certificate())

        return result
