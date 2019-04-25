
from Acquire.Client import PublicKey, Authorisation

from Acquire.Storage import DriveInfo, ACLRules


def run(args):
    """This function is used to initiate a bulk upload of lots
       of files to the storage service. The process is as follows;

       (1) The user initiates a bulk upload, specifying the maximum
           size of all of the files to be uploaded, and the bucket in
           which all of the files will eventually be placed

       (2) We create a temporary bucket that will house all of the
           uploaded files, and return to the user a PAR that can
           be used to write arbitrary files to the bucket.

       (3) When the user closes the PAR (or when it expires) we will
           verify that the total size of all of the files does not
           exceed 'max_size' and will then copy them into the drive
           specified by the user as the eventual home of the files.
           Once all of the files have been securely copied then
           the bucket will be deleted.

        This process is used as the bulk upload PAR provides arbitrary
        write access, and so we have to isolate this from all other
        users
    """
    authorisation = Authorisation.from_data(args["authorisation"])
    drive_uid = str(args["drive_uid"])
    encrypt_key = PublicKey.from_data(args["encrypt_key"])

    aclrules = None

    if "aclrules" in args:
        try:
            aclrules = ACLRules.from_data(args["aclrules"])
        except:
            try:
                aclrules = ACLRule.from_data(args["aclrules"])
                aclrules = ACLRules(default_rule=aclrules)
            except:
                pass

    try:
        max_size = int(args["max_size"])
    except:
        max_size = None

    par = None

    drive = DriveInfo(drive_uid=drive_uid)

    par = drive.bulk_upload(authorisation=authorisation,
                            encrypt_key=encrypt_key,
                            max_size=max_size,
                            aclrules=aclrules)

    return_value = {}

    if par is not None:
        return_value["bulk_upload_par"] = par.to_data()

    return return_value
