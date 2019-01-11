
import lazy_import as _lazy_import

_hashlib = _lazy_import.lazy_module("hashlib")

__all__ = ["get_filesize_and_checksum"]


def get_filesize_and_checksum(filename):
    """Return a tuple of the size in bytes of the passed file and the
       file's md5 checksum
    """
    md5 = _hashlib.md5()
    size = 0

    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
            size += len(chunk)

    return (size, str(md5.hexdigest()))
