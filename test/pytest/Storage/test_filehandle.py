
import pytest

from Acquire.Client import FileHandle


def test_filehandle():
    filename = __file__

    f1 = FileHandle(filename=filename, drive_uid="test_uid")

    data = f1.to_data()

    f2 = FileHandle.from_data(data)

    assert(f1.filesize() == f2.filesize())
    assert(f1.checksum() == f2.checksum())
    assert(f1.is_compressed() == f2.is_compressed())
    assert(f1.compression_type() == f2.compression_type())
    assert(f1.is_localdata() == f2.is_localdata())
    assert(f1.local_filedata() == f2.local_filedata())
    assert(f1.fingerprint() == f2.fingerprint())
    assert(f1.drive_uid() == f2.drive_uid())
