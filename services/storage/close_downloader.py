
from Acquire.Storage import DriveInfo


def run(args):
    """Close the downloader for a file - this stops new chunks
       being downloaded using this object
    """

    uid = str(args["uid"])
    drive_uid = str(args["drive_uid"])
    file_uid = str(args["file_uid"])
    secret = str(args["secret"])

    drive = DriveInfo(drive_uid=drive_uid)

    drive.close_downloader(file_uid=file_uid, downloader_uid=uid,
                           secret=secret)

    return True
