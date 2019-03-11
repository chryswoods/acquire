
from Acquire.Service import create_return_value

from Acquire.Identity import Authorisation

from Acquire.Storage import FileInfo, DriveInfo

from Acquire.Crypto import PublicKey

from Acquire.ObjectStore import ObjectStore


def run(args):
    """Call this function to initiate the two-step file-upload process.

       Step 1: upload_file - tells the service that a file of specific
               size and checksum will be uploaded. This gives the service
               the chance to decide whether this will be allowed, and if
               so, it returns a PAR that can be used for this upload

       Step 2: uploaded_file - after the user has used the PAR to upload
               the file, they should call this function to notify
               the service that the file has been successfully uploaded.
               This will verify that the file has been uploaded correctly,
               will receipt the storage cost and will delete the PAR
    """

    drive_uid = args["drive_uid"]
    fileinfo = FileInfo.from_data(args["fileinfo"])
    authorisation = Authorisation.from_data(args["authorisation"])
    public_key = PublicKey.from_data(args["encryption_key"])

    drive = DriveInfo(drive_uid=drive_uid, user_guid=authorisation.user_guid())

    par = drive.get_upload_par(fileinfo=fileinfo, authorisation=authorisation,
                               encrypt_key=public_key)

    return_value = create_return_value()

    return_value["upload_par"] = par.to_data()

    return return_value
