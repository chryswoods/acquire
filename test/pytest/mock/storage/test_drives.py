

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

    print(drive2)
    print(drives)

    assert(len(drives) == 1)

    drives = drive.list_drives()

    assert(len(drives) == 0)

    filename = __file__

    files = drive.list_files()
    assert(len(files) == 0)

    filehandle = drive.upload(filename=filename)

    (_, filename) = os.path.split(filename)

    assert(filehandle.filename() == filename)

    files = drive.list_files()

    assert(len(files) == 1)

    assert(files[0].filename() == filename)
