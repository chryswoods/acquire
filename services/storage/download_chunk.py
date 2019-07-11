
from Acquire.Storage import DriveInfo
from Acquire.ObjectStore import bytes_to_string

import json


def run(args):
    """Download a chunk of data from a file"""

    uid = str(args["uid"])
    drive_uid = str(args["drive_uid"])
    file_uid = str(args["file_uid"])
    chunk_idx = int(args["chunk_index"])
    secret = str(args["secret"])

    drive = DriveInfo(drive_uid=drive_uid)

    try:
        (data, meta, num_chunks) = drive.download_chunk(file_uid=file_uid,
                                                        downloader_uid=uid,
                                                        chunk_index=chunk_idx,
                                                        secret=secret)
    except IndexError:
        data = None
        meta = None
        num_chunks = None

    response = {}

    if data is not None:
        response["chunk"] = bytes_to_string(data)
        data = None

    if meta is not None:
        response["meta"] = json.dumps(meta)

    if num_chunks is not None:
        response["num_chunks"] = int(num_chunks)

    return response
