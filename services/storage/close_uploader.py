
from Acquire.Storage import DriveInfo


def run(args):
    """Close the uploader for a file - this stops new chunks being uploaded"""

    drive_uid = str(args["drive_uid"])
    file_uid = str(args["file_uid"])
    secret = str(args["secret"])

    drive = DriveInfo(drive_uid=drive_uid)

    drive.close_uploader(file_uid=file_uid, secret=secret)

    return True
