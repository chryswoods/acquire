
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

    try:
        name = args["name"]
    except:
        name = None

    try:
        autocreate = args["autocreate"]

        if autocreate is False:
            autocreate = False
        else:
            autocreate = True
    except:
        autocreate = True

    drives = UserDrives(authorisation=authorisation)

    infos = {}

    if name is None:
        for name in drives.list_drives():
            drive_info = drives.get_drive(name=name, autocreate=False)
            infos[name] = {"drive_uid": drive_info.uid(),
                           "acl": drive_info.get_acl(
                                authorisation.user_guid()).to_data()}
    else:
        drive_info = drives.get_drive(name=name, autocreate=autocreate)
        infos[name] = {"drive_uid": drive_info.uid(),
                       "acl": drive_info.get_acl(
                                authorisation.user_guid()).to_data()}

    message = "success"
    return_value = create_return_value(status, message)

    return_value["drives"] = infos

    return return_value
