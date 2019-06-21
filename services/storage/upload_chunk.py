
from Acquire.Storage import DriveInfo
from Acquire.ObjectStore import string_to_bytes


def run(args):
    """Upload a new chunk of data to a file"""

    drive_uid = str(args["drive_uid"])
    file_uid = str(args["file_uid"])
    chunk_idx = int(args["chunk_index"])
    secret = str(args["secret"])
    data = string_to_bytes(args["data"])
    checksum = str(args["checksum"])

    drive = DriveInfo(drive_uid=drive_uid)

    drive.upload_chunk(file_uid=file_uid, chunk_index=chunk_idx,
                       secret=secret, chunk=data, checksum=checksum)

    return True
