
from Acquire.Identity import Authorisation

from Acquire.Storage import DriveInfo

from Acquire.Client import FileHandle, FileMeta, PAR

from Acquire.Crypto import PublicKey


def run(args):
    """Call this function to initiate the two-step file-upload process.

       Step 1: upload - tells the service that a file of specific
               size and checksum will be uploaded. This gives the service
               the chance to decide whether this will be allowed. If the
               file is small, and was thus included in the FileHandle,
               then it is uploaded immediately and the operation completes.
               If the file is large, then we now returns a PAR
               that can be used for this upload (Step 2)

       Step 2: after the user has used the PAR to upload
               the file, they should call PAR.close() to notify
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

    drive = DriveInfo(drive_uid=drive_uid)

    return_value = {}

    (filemeta, par) = drive.upload(filehandle=filehandle,
                                   authorisation=authorisation,
                                   encrypt_key=public_key)

    if filemeta is not None:
        return_value["filemeta"] = filemeta.to_data()

    if par is not None:
        return_value["upload_par"] = par.to_data()

    return return_value
