
import pytest

from Acquire.Client import PAR, Location, ACLRule, Drive, StorageCreds


@pytest.fixture(scope="session")
def tempdir(tmpdir_factory):
    d = tmpdir_factory.mktemp("")
    return str(d)


def _same_file(file1, file2):
    lines1 = open(file1, "r").readlines()
    lines2 = open(file2, "r").readlines()

    return lines1 == lines2


def test_drive_par(authenticated_user, tempdir):
    drive_name = "test å∫ç∂ pars"
    creds = StorageCreds(user=authenticated_user, service_url="storage")

    drive = Drive(name=drive_name, creds=creds)

    drive.upload(filename=__file__, uploaded_name="tmp_test.py")

    downloaded_name = drive.download(filename="tmp_test.py", dir=tempdir)

    assert(_same_file(__file__, downloaded_name))

    drive_guid = drive.metadata().guid()

    location = Location(drive_guid=drive_guid)

    par = PAR(location=location, user=authenticated_user,
              aclrule=ACLRule.reader())

    par_drive = par.resolve()
    assert(par_drive.metadata().acl() == ACLRule.reader())
    assert(par_drive.metadata().uid() == drive.metadata().uid())

    files = par_drive.list_files()
    assert(len(files) == 1)
    assert(files[0].filename() == "tmp_test.py")

    downloaded_name = files[0].open().download(dir=tempdir,
                                               force_par=True)

    assert(_same_file(__file__, downloaded_name))

    par2 = PAR(location=location, user=authenticated_user,
               aclrule=ACLRule.writer())

    par_drive = par2.resolve()

    assert(par_drive.metadata().acl() == ACLRule.writer())
    assert(par_drive.metadata().uid() == drive.metadata().uid())

    files = par_drive.list_files()
    assert(len(files) == 1)
    assert(files[0].filename() == "tmp_test.py")

    par_drive.upload(filename=__file__, uploaded_name="tmp_test2.py")

    files = par_drive.list_files()
    assert(len(files) == 2)
    f = {}
    f[files[0].filename()] = files[0]
    f[files[1].filename()] = files[1]
    files = f

    assert("tmp_test.py" in files)
    assert("tmp_test2.py" in files)

    downloaded_name = files["tmp_test2.py"].open().download(dir=tempdir)

    assert(_same_file(__file__, downloaded_name))

    par = PAR(location=files["tmp_test.py"].location(),
              user=authenticated_user,
              aclrule=ACLRule.reader())

    par_file = par.resolve()

    assert(par_file.metadata().acl() == ACLRule.reader())

    downloaded_name = par_file.download(dir=tempdir)

    assert(_same_file(__file__, downloaded_name))

    with pytest.raises(PermissionError):
        par_file.upload(__file__)

    par = PAR(location=files["tmp_test.py"].location(),
              user=authenticated_user,
              aclrule=ACLRule.writer())

    par_file = par.resolve()

    assert(par_file.metadata().acl() == ACLRule.writer())

    par_file.upload(__file__)
