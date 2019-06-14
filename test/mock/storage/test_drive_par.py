
import pytest

from Acquire.Client import PAR, Location, ACLRule, Drive


@pytest.fixture(scope="session")
def tempdir(tmpdir_factory):
    d = tmpdir_factory.mktemp("")
    return str(d)


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

    print(par_drive)

    files = par_drive.list_files()
    print(files)

    assert(par_drive.acl() == ACLRule.reader())
    assert(par_drive.uid() == drive.uid())

    assert(False)
