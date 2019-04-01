

import pytest
import os

from Acquire.Client import Drive


@pytest.fixture(scope="session")
def tempdir(tmpdir_factory):
    d = tmpdir_factory.mktemp("")
    return str(d)


def test_drives(authenticated_user, tempdir):

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
    assert(filemeta.uploaded_by() == authenticated_user.guid())
    assert(filemeta.uploaded_when() is not None)

    upload_datetime = filemeta.uploaded_when()

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
    assert(files[0].uploaded_by() == authenticated_user.guid())
    assert(files[0].uploaded_when() == upload_datetime)

    (filename, filemeta) = drive.download(files[0].filename(), dir=tempdir)

    # make sure that the two files are identical
    with open(filename, "rb") as FILE:
        data1 = FILE.read()

    # remove this tmp file
    os.unlink(filename)

    with open(__file__, "rb") as FILE:
        data2 = FILE.read()

    assert(data1 == data2)

    assert(files[0].uid() == filemeta.uid())
    assert(files[0].filesize() == filemeta.filesize())
    assert(files[0].checksum() == filemeta.checksum())
    assert(files[0].compression_type() == filemeta.compression_type())
    assert(files[0].uploaded_by() == filemeta.uploaded_by())
    assert(files[0].uploaded_when() == filemeta.uploaded_when())
    assert(files[0].acl().is_owner())
    assert(files[0].uploaded_by() == authenticated_user.guid())
    assert(files[0].uploaded_when() == upload_datetime)

    versions = drive.list_versions(filename=filemeta.filename())

    assert(len(versions) == 1)
    assert(versions[0].filename() == filemeta.filename())
    assert(versions[0].uploaded_when() == filemeta.uploaded_when())

    versions = drive.list_versions(filename=filemeta.filename(),
                                   include_metadata=True)

    assert(len(versions) == 1)
    assert(versions[0].filename() == filemeta.filename())
    assert(versions[0].uploaded_when() == filemeta.uploaded_when())

    assert(versions[0] == filemeta)

    new_filemeta = drive.upload(filename=__file__)

    versions = drive.list_versions(filename=filemeta.filename())

    assert(len(versions) == 2)

    versions = drive.list_versions(filename=filemeta.filename(),
                                   include_metadata=True)

    assert(len(versions) == 2)

    (filename, new_filemeta) = drive.download(filemeta.filename(), dir=tempdir)

    # make sure that the two files are identical
    with open(filename, "rb") as FILE:
        data1 = FILE.read()

    # remove this tmp file
    os.unlink(filename)

    with open(__file__, "rb") as FILE:
        data2 = FILE.read()

    assert(data1 == data2)

    # should be in upload order
    assert(versions[0] == filemeta)
    assert(versions[1] == new_filemeta)
