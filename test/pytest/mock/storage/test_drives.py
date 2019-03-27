

import pytest
import os

from Acquire.Client import Drive


def test_drives(authenticated_user):

    drive_name = "test å∫ç∂ something"
    drive = Drive(user=authenticated_user, name=drive_name,
                  storage_url="storage")

    assert(drive.name() == drive_name)
    assert(drive.acl().is_owner())

    drive2_name = "test/this/is/a/../../dir"

    drive2 = Drive(user=authenticated_user, name=drive2_name,
                   storage_url="storage")

    drives = Drive.list_toplevel_drives(user=authenticated_user,
                                        storage_url="storage")

    assert(len(drives) == 2)

    drives = drive2.list_drives()

    assert(len(drives) == 0)

    drives = drive.list_drives()

    assert(len(drives) == 0)

    filename = __file__

    files = drive.list_files()
    assert(len(files) == 0)

    filemeta = drive.upload(filename=filename)

    assert(filemeta.has_metadata())
    assert(filemeta.acl().is_owner())
    assert(filemeta.acl().is_readable())
    assert(filemeta.acl().is_writeable())

    (_, filename) = os.path.split(filename)

    assert(filemeta.filename() == filename)

    files = drive.list_files()

    assert(len(files) == 1)

    assert(files[0].filename() == filemeta.filename())
    assert(not files[0].has_metadata())

    files = drive.list_files(include_metadata=True)

    assert(len(files) == 1)

    assert(files[0].filename() == filemeta.filename())
    assert(files[0].has_metadata())

    assert(files[0].uid() == filemeta.uid())
    assert(files[0].filesize() == filemeta.filesize())
    assert(files[0].checksum() == filemeta.checksum())
    assert(files[0].compression_type() == filemeta.compression_type())
    assert(files[0].uploaded_by() == filemeta.uploaded_by())
    assert(files[0].uploaded_when() == filemeta.uploaded_when())
    assert(files[0].acl().is_owner())

    filemeta = drive.download(files[0].filename())
