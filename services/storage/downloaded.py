
from Acquire.Client import Authorisation

from Acquire.Storage import DriveInfo

from Acquire.Service import create_return_value


def run(args):
    """Call this function to complete the two-step process to download
       a file. This function is called once the PAR has been used
       to download the file. It deletes the PAR, ensuring it cannot
       be used by anyone else
    """

    drive_uid = str(args["drive_uid"])
    authorisation = Authorisation.from_data(args["authorisation"])
    par_uid = str(args["par_uid"])

    drive = DriveInfo(drive_uid=drive_uid, user_guid=authorisation.user_guid())

    drive.download_complete(par_uid=par_uid,
                            authorisation=authorisation)

    return_value = create_return_value()

    return return_value
