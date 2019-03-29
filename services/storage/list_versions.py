
from Acquire.Service import create_return_value

from Acquire.Storage import DriveInfo

from Acquire.Client import Authorisation

from Acquire.ObjectStore import list_to_string


def run(args):
    """This file is used to return a list of versions of the
       specified filenames
    """

    drive_uid = str(args["drive_uid"])
    authorisation = Authorisation.from_data(args["authorisation"])
    filename = args["filename"]

    try:
        include_metadata = args["include_metadata"]
    except:
        include_metadata = False

    if include_metadata:
        include_metadata = True
    else:
        include_metadata = False

    drive = DriveInfo(drive_uid=drive_uid, user_guid=authorisation.user_guid())

    versions = drive.list_versions(authorisation=authorisation,
                                   filename=filename,
                                   include_metadata=include_metadata)

    return_value = create_return_value()

    return_value["versions"] = list_to_string(versions)

    return return_value
