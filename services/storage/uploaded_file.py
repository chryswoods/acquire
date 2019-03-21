
from Acquire.Client import Authorisation

from Acquire.Storage import DriveInfo

from Acquire.Service import create_return_value


def run(args):
    """Call this function to complete the two-step process to upload
       a file. This function is called once the PAR has been used
       to upload the file. This verifies that the file has been
       uploaded correctly. It then deletes the PAR and receipts
       the payment
    """

    drive_uid = str(args["drive_uid"])
    authorisation = Authorisation.from_data(args["authorisation"])
    par_uid = str(args["par_uid"])

    drive = DriveInfo(drive_uid=drive_uid, user_guid=authorisation.user_guid())

    fileinfo = drive.par_upload_complete(par_uid=par_uid,
                                         authorisation=authorisation)

    return_value = create_return_value()

    return_value["fileinfo"] = fileinfo.to_data()

    return return_value
