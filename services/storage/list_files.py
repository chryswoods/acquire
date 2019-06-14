
from Acquire.Storage import DriveInfo, UserDrives, PARRegistry

from Acquire.Client import Authorisation

from Acquire.ObjectStore import list_to_string


def run(args):
    """This file is used to return a list of the FileMeta objects of files
       that are in a specified drive
    """

    drive_uid = str(args["drive_uid"])

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        authorisation = None

    try:
        par_uid = args["par_uid"]
    except:
        par_uid = None

    try:
        secret = args["secret"]
    except:
        secret = None

    try:
        include_metadata = args["include_metadata"]
    except:
        include_metadata = False

    if include_metadata:
        include_metadata = True
    else:
        include_metadata = False

    if par_uid is not None:
        registry = PARRegistry()
        (par, identifiers) = registry.load(par_uid=par_uid, secret=secret)

    drive = DriveInfo(drive_uid=drive_uid)

    files = drive.list_files(authorisation=authorisation,
                             include_metadata=include_metadata,
                             par=par, identifiers=identifiers)

    return_value = {}

    return_value["files"] = list_to_string(files)

    return return_value
