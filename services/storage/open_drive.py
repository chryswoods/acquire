
from Acquire.Identity import Authorisation, ACLRules

from Acquire.Storage import UserDrives, DriveInfo


def run(args):
    """Call this function to open and return a handle to the
       user's requested CloudDrive. This will create the
       drive (and the all intermediate drives) unless the
       user sets autocreate to false
    """

    authorisation = Authorisation.from_data(args["authorisation"])
    name = args["name"]

    try:
        autocreate = args["autocreate"]

        if autocreate is False:
            autocreate = False
        else:
            autocreate = True
    except:
        autocreate = True

    if autocreate and "aclrules" in args:
        aclrules = ACLRules.from_data(args["aclrules"])
    else:
        aclrules = None

    drives = UserDrives(authorisation=authorisation)

    drive = drives.get_drive(name=name, aclrules=aclrules,
                             autocreate=autocreate)

    return_value = {}

    return_value["drive"] = drive.to_data()

    return return_value
