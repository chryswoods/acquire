
from Acquire.Storage import ACLRules, DriveInfo, PARRegistry
from Acquire.Client import Authorisation, PAR
from Acquire.Crypto import PublicKey


def run(args):
    """Open and return a new ChunkUploader that can be used
       to upload a file in lots of chunks
    """

    filename = str(args["filename"])
    drive_uid = str(args["drive_uid"])

    try:
        aclrules = ACLRules.from_data(args["aclrules"])
    except:
        aclrules = None

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        authorisation = None

    try:
        par_uid = str(args["par_uid"])
    except:
        par_uid = None

    try:
        secret = str(args["secret"])
    except:
        secret = None

    try:
        pubkey = PublicKey.from_data(args["encryption_key"])
    except:
        pubkey = None

    if par_uid is not None:
        registry = PARRegistry()
        (par, identifiers) = registry.load(par_uid=par_uid, secret=secret)
    else:
        par = None
        identifiers = None

    drive = DriveInfo(drive_uid=drive_uid)

    (filemeta, uploader) = drive.open_uploader(
                                   filename=filename, aclrules=aclrules,
                                   authorisation=authorisation,
                                   par=par, identifiers=identifiers)

    return {"filemeta": filemeta.to_data(),
            "uploader": uploader.to_data(pubkey=pubkey)}
