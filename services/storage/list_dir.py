
from Acquire.Service import create_return_value

from Acquire.ObjectStore import dict_to_string

from Acquire.Storage import DriveInfo

from Acquire.Client import Authorisation


def run(args):
    """This file is used to return a list of the contents of a specified
       directory in a drive
    """

    drive_uid = str(args["drive_uid"])
    recursive = args["recursive"]
    dirname = args["dirname"]
    authorisation = Authorisation.from_data(args["authorisation"])

    if recursive:
        recursive = True
    else:
        recursive = False

    if dirname is not None:
        dirname = str(dirname)

    drive = DriveInfo(drive_uid=drive_uid, user_guid=authorisation.user_guid())

    fileinfos = drive.list_dir(dirname=dirname, recursive=recursive,
                               authorisation=authorisation)

    return_value = create_return_value()

    return_value["fileinfos"] = dict_to_string(fileinfos)

    return return_value
