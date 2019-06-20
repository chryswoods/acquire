
from Acquire.Identity import Authorisation

from Acquire.Storage import DriveInfo, PARRegistry

from Acquire.Crypto import PublicKey


def run(args):
    """Call this function to initiate the two-step file-download process.

       Step 1: download - tells the service to download the file. If the
               file is small then the file will be in the response.
               Otherwise a OSPar will be returned that will let you
               download the file. If this is the case, then you must
               call step 2...

       Step 2: downloaded - after you have downloaded the file from the OSPar
               call OSPar.close() so that the service knows that the OSPar
               is no longer needed and can be deleted
    """

    drive_uid = args["drive_uid"]
    filename = args["filename"]

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

    public_key = PublicKey.from_data(args["encryption_key"])

    if "version" in args:
        version = str(args["version"])
    else:
        version = None

    if "force_par" in args:
        force_par = args["force_par"]
    else:
        force_par = None

    if force_par:
        force_par = True

    if par_uid is not None:
        registry = PARRegistry()
        (par, identifiers) = registry.load(par_uid=par_uid, secret=secret)
    else:
        par = None
        identifiers = None

    drive = DriveInfo(drive_uid=drive_uid)

    return_value = {}

    (filemeta, filedata, par, downloader) = drive.download(
                                               filename=filename,
                                               version=version,
                                               authorisation=authorisation,
                                               encrypt_key=public_key,
                                               force_par=force_par,
                                               par=par,
                                               identifiers=identifiers)

    if filemeta is not None:
        return_value["filemeta"] = filemeta.to_data()

    if filedata is not None:
        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
        return_value["filedata"] = _bytes_to_string(filedata)

    if par is not None:
        return_value["download_par"] = par.to_data()

    if downloader is not None:
        return_value["downloader"] = downloader.to_data(pubkey=public_key)

    return return_value
