
from Acquire.Service import create_return_value

from Acquire.Identity import Authorisation

from Acquire.Storage import DriveInfo

from Acquire.Client import FileHandle, PAR

from Acquire.Crypto import PublicKey


def run(args):
    """Call this function to initiate the two-step file-download process.

       Step 1: download - tells the service to download the file. If the
               file is small then the file will be in the response.
               Otherwise a PAR will be returned that will let you
               download the file. If this is the case, then you must
               call step 2...

       Step 2: downloaded - after you have downloaded the file from the PAR
               call PAR.close() so that the service knows that the PAR
               is no longer needed and can be deleted
    """

    drive_uid = args["drive_uid"]
    filename = args["filename"]
    authorisation = Authorisation.from_data(args["authorisation"])
    public_key = PublicKey.from_data(args["encryption_key"])

    if "version" in args:
        from Acquire.ObjectStore import string_to_datetime \
            as _string_to_datetime
        version = _string_to_datetime(args["version"])
    else:
        version = None

    drive = DriveInfo(drive_uid=drive_uid,
                      user_guid=authorisation.user_guid())

    return_value = create_return_value()

    (filemeta, filedata, par) = drive.download(filename=filename,
                                               version=version,
                                               authorisation=authorisation,
                                               encrypt_key=public_key)

    if filemeta is not None:
        return_value["filemeta"] = filemeta.to_data()

    if filedata is not None:
        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
        return_value["filedata"] = _bytes_to_string(filedata)

    if par is not None:
        return_value["download_par"] = par.to_data()

    return return_value
