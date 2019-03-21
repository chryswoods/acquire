

import pytest
import os

from Acquire.Client import Drive


def test_drives(authenticated_user):

    drive_name = "test å∫ç∂ something"
    drive = Drive(user=authenticated_user, name=drive_name,
                  storage_url="storage")

    assert(drive.name() == drive_name)
    assert(drive.acl().is_owner())

    filename = __file__

    filehandle = drive.upload(filename=filename)

    (root, filename) = os.path.split(filename)

    assert(filehandle.filename() == filename)
