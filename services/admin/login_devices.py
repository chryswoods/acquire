
from Acquire.Service import get_this_service

from Acquire.Identity import UserCredentials


def run(args):
    """This function is used to list and manage the login devices
       available for a user account.
    """

    user_uid = args["user_uid"]

    devices = UserCredentials.list_devices(user_uid=user_uid)

    print(devices)

    return devices
