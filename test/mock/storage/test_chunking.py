
import pytest

from Acquire.Client import Drive, StorageCreds


@pytest.fixture(scope="session")
def tempdir(tmpdir_factory):
    d = tmpdir_factory.mktemp("")
    return str(d)


def _same_file(file1, file2):
    lines1 = open(file1, "r").readlines()
    lines2 = open(file2, "r").readlines()

    return lines1 == lines2


def test_chunking(authenticated_user, tempdir):
    drive_name = "test_chunking"
    creds = StorageCreds(user=authenticated_user, service_url="storage")

    drive = Drive(name=drive_name, creds=creds)

    uploader = drive.chunk_upload("test_chunking.py")

    uploader.upload("This is some text\n")
    uploader.upload("Here is")
    uploader.upload(" some more!\n")

    uploader.close()

    filename = drive.download("test_chunking.py", dir=tempdir)

    lines = open(filename).readlines()

    assert(lines[0] == "This is some text\n")
    assert(lines[1] == "Here is some more!\n")
