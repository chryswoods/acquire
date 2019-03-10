
from Acquire.Service import create_return_value

from Acquire.Identity import Authorisation

from Acquire.Storage import UserDrives, DriveInfo


def run(args):
    """Call this function to open and return a handle to the
       user's requested CloudDrive. This will create a drive
       with that name unless the user has specifically requested
       not to
    """

    status = 0
    message = None

    authorisation = Authorisation.from_data(args["authorisation"])
    name = args["name"]

    try:
        autocreate = args["autocreate"]

        if autocreate is False:
            autocreate = False
        else:
            autocreate = True
    except:
        autocreate = True

    drives = UserDrives(authorisation=authorisation)
    drive_info = drives.get_drive(name=name, autocreate=autocreate)

    message = "success"
    return_value = create_return_value(status, message)

    return_value["drive_info"] = drive_info.to_data()

    return return_value
