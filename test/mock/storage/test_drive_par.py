
import pytest

from Acquire.Client import PAR, Identifier, ACLRule, Drive


@pytest.fixture(scope="session")
def tempdir(tmpdir_factory):
    d = tmpdir_factory.mktemp("")
    return str(d)


def test_drive_par(authenticated_user, tempdir):
    drive_name = "test å∫ç∂ something"
    drive = Drive(user=authenticated_user, name=drive_name,
                  storage_url="storage")

    drive_guid = drive.guid()

    iden = Identifier(drive_guid=drive_guid)

    par = PAR(identifier=iden, user=authenticated_user,
              aclrule=ACLRule.reader())

    drive = par.resolve()
