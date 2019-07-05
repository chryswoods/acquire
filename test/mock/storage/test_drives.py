

import pytest
import os

from Acquire.Client import Drive, StorageCreds, ACLRules
from Acquire.ObjectStore import OSPar


@pytest.fixture(scope="session")
def tempdir(tmpdir_factory):
    d = tmpdir_factory.mktemp("")
    return str(d)


def test_drives(authenticated_user, tempdir):

    creds = StorageCreds(user=authenticated_user, service_url="storage")

    nstart = len(Drive.list_toplevel_drives(creds=creds))

    drive_name = "test å∫ç∂ something"
    drive = Drive(name=drive_name, creds=creds, autocreate=True)

    assert(drive.metadata().name() == drive_name)
    assert(drive.metadata().acl().is_owner())

    drive2_name = "test/this/is/a/../../dir"

    drive2 = Drive(name=drive2_name, creds=creds)

    drives = Drive.list_toplevel_drives(creds=creds)

    assert(len(drives) == nstart + 2)

    drives = drive2.list_drives()

    assert(len(drives) == 0)

    drives = drive.list_drives()

    assert(len(drives) == 0)

    filename = __file__

    files = drive.list_files()
    assert(len(files) == 0)

    filemeta = drive.upload(filename=filename)

    assert(filemeta.is_complete())
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
    assert(not files[0].is_complete())

    files = drive.list_files(include_metadata=True)

    assert(len(files) == 1)

    assert(files[0].filename() == filemeta.filename())
    assert(files[0].is_complete())

    assert(files[0].uid() == filemeta.uid())
    assert(files[0].filesize() == filemeta.filesize())
    assert(files[0].checksum() == filemeta.checksum())
    assert(files[0].compression_type() == filemeta.compression_type())
    assert(files[0].uploaded_by() == filemeta.uploaded_by())
    assert(files[0].uploaded_when() == filemeta.uploaded_when())
    assert(files[0].acl().is_owner())
    assert(files[0].uploaded_by() == authenticated_user.guid())
    assert(files[0].uploaded_when() == upload_datetime)

    f = files[0].open()
    filename = f.download(dir=tempdir)

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

    versions = f.list_versions()

    assert(len(versions) == 1)
    assert(versions[0].filename() == filemeta.filename())
    assert(versions[0].uploaded_when() == filemeta.uploaded_when())

    new_filemeta = drive.upload(filename=__file__, force_par=True)

    versions = f.list_versions()

    assert(len(versions) == 2)

    filename = new_filemeta.open().download(dir=tempdir)

    # make sure that the two files are identical
    with open(filename, "rb") as FILE:
        data1 = FILE.read()

    # remove this tmp file
    os.unlink(filename)

    with open(__file__, "rb") as FILE:
        data2 = FILE.read()

    assert(data1 == data2)

    # should be in upload order
    assert(versions[0].uid() == filemeta.uid())
    assert(versions[1].uid() == new_filemeta.uid())

    filename = new_filemeta.open().download(dir=tempdir, force_par=True)

    # make sure that the two files are identical
    with open(filename, "rb") as FILE:
        data1 = FILE.read()

    # remove this tmp file
    os.unlink(filename)

    assert(data1 == data2)

    # try to upload a file with path to the drive
    filemeta = drive.upload(filename=__file__,
                            uploaded_name="/test/one/../two/test.py")

    assert(filemeta.filename() == "test/two/test.py")

    # cannot create a new Drive with non-owner ACLs
    with pytest.raises(PermissionError):
        drive = Drive(name="broken_acl", creds=creds,
                      aclrules=ACLRules.owner("12345@z0-z0"))

    drive = Drive(name="working_acl", creds=creds,
                  aclrules=ACLRules.owner(authenticated_user.guid()))
