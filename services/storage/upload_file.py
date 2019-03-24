
from Acquire.Service import create_return_value

from Acquire.Identity import Authorisation

from Acquire.Storage import DriveInfo

from Acquire.Client import FileHandle, FileMeta, PAR

from Acquire.Crypto import PublicKey


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

    filehandle = FileHandle.from_data(args["filehandle"])
    authorisation = Authorisation.from_data(args["authorisation"])

    try:
        public_key = PublicKey.from_data(args["encryption_key"])
    except:
        public_key = None

    drive_uid = filehandle.drive_uid()

    drive = DriveInfo(drive_uid=drive_uid,
                      user_guid=authorisation.user_guid())

    return_value = create_return_value()

    result = drive.upload_file(filehandle=filehandle,
                               authorisation=authorisation,
                               encrypt_key=public_key)

    if isinstance(result, PAR):
        return_value["upload_par"] = result.to_data()
    elif isinstance(result, FileMeta):
        return_value["filemeta"] = result.to_data()
    else:
        raise TypeError("Unrecognised upload return type: %s" % result)

    return return_value
