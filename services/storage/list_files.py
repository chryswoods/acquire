
from Acquire.Service import create_return_value

from Acquire.Storage import DriveInfo, UserDrives

from Acquire.Client import Authorisation

from Acquire.ObjectStore import list_to_string


def run(args):
    """This file is used to return a list of the FileMeta objects of files
       that are in a specified drive
    """

    drive_uid = str(args["drive_uid"])
    authorisation = Authorisation.from_data(args["authorisation"])

    try:
        include_metadata = args["include_metadata"]
    except:
        include_metadata = False

    if include_metadata:
        include_metadata = True
    else:
        include_metadata = False

    drive = DriveInfo(drive_uid=drive_uid)

    files = drive.list_files(authorisation=authorisation,
                             include_metadata=include_metadata)

    return_value = create_return_value()

    return_value["files"] = list_to_string(files)

    return return_value
