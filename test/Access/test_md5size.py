
from Acquire.Access import get_filesize_and_checksum

import pytest
import os

from hashlib import md5

def _get_size(filename):
    """Return the file size in bytes"""
    return os.path.getsize(filename)


def _get_md5(filename):
    """Return the MD5 checksum of the passed file"""
    data = open(filename, "rb").read()
    r = md5(data)
    return r.hexdigest()


def test_md5size():
    # test by calculating sizes and md5s of all files in
    # the current directory
    for filename in os.listdir("."):
        if os.path.isfile(filename):
            (filesize, md5) = get_filesize_and_checksum(filename)

            checksize = _get_size(filename)
            checkmd5 = _get_md5(filename)

            assert(filesize == checksize)
            assert(md5 == checkmd5)
