
import pytest

from Acquire.Client import PAR, Location, ACLRule, Drive


@pytest.fixture(scope="session")
def tempdir(tmpdir_factory):
    d = tmpdir_factory.mktemp("")
    return str(d)


def _same_file(file1, file2):
    lines1 = open(file1, "r").readlines()
    lines2 = open(file2, "r").readlines()

    return lines1 == lines2


def test_drive_par(authenticated_user, tempdir):
    drive_name = "test å∫ç∂ something"
    drive = Drive(user=authenticated_user, name=drive_name,
                  storage_url="storage")

    drive.upload(filename=__file__, uploaded_name="tmp_test.py")

    drive_guid = drive.guid()

    location = Location(drive_guid=drive_guid)

    par = PAR(location=location, user=authenticated_user,
              aclrule=ACLRule.reader())

    par_drive = par.resolve()
    assert(par_drive.acl() == ACLRule.reader())
    assert(par_drive.uid() == drive.uid())

    files = par_drive.list_files()
    assert(len(files) == 1)
    assert(files[0].filename() == "tmp_test.py")

    (downloaded_name, filemeta) = par_drive.download("tmp_test.py",
                                                     dir=tempdir,
                                                     force_par=True)

    assert(filemeta.filename() == "tmp_test.py")
    assert(_same_file(__file__, downloaded_name))

    par2 = PAR(location=location, user=authenticated_user,
               aclrule=ACLRule.writer())

    par_drive = par2.resolve()

    assert(par_drive.acl() == ACLRule.writer())
    assert(par_drive.uid() == drive.uid())

    files = par_drive.list_files()
    assert(len(files) == 1)
    assert(files[0].filename() == "tmp_test.py")

    par_drive.upload(filename=__file__, uploaded_name="tmp_test2.py")

    files = par_drive.list_files()
    assert(len(files) == 2)
    assert(files[0].filename() == "tmp_test.py")
    assert(files[1].filename() == "tmp_test2.py")

    (downloaded_name, filemeta) = par_drive.download("tmp_test2.py",
                                                     dir=tempdir,
                                                     force_par=True)

    assert(filemeta.filename() == "tmp_test2.py")
    assert(_same_file(__file__, downloaded_name))
