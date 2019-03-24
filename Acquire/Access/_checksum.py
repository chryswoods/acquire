
__all__ = ["get_filesize_and_checksum", "get_size_and_checksum"]


def get_size_and_checksum(data):
    """Return a tuple of the size in bytes of the passed data and the
       data's md5 checksum
    """
    from hashlib import md5 as _md5
    md5 = _md5()
    md5.update(data)

    return (len(data), str(md5.hexdigest()))


def get_filesize_and_checksum(filename):
    """Return a tuple of the size in bytes of the passed file and the
       file's md5 checksum
    """
    from hashlib import md5 as _md5
    md5 = _md5()
    size = 0

    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
            size += len(chunk)

    return (size, str(md5.hexdigest()))
