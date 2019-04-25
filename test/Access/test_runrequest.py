
from Acquire.Access import Request, RunRequest, get_filesize_and_checksum

import pytest
import os
import sys
import tarfile


def _testdata():
    """Return the path to the directory containing test data"""
    return os.path.dirname(os.path.abspath(__file__)) + \
        os.path.sep + "testdata"


@pytest.fixture(scope="session")
def tempdir(tmpdir_factory):
    d = tmpdir_factory.mktemp("")
    return str(d)


def _test_request(request, tempdir):
    t = tarfile.TarFile(name=request.tarfile(), mode="r")

    t.extractall(path=tempdir)

    filenames = {}

    for (key, fileinfo) in request.input_files().items():
        (filename, filesize, md5) = fileinfo

        (s, m) = get_filesize_and_checksum("%s/%s" % (tempdir, filename))

        assert(s == filesize)
        assert(m == md5)

        filenames[filename] = 1

    for filename in os.listdir(tempdir):
        if os.path.isfile(filename):
            if filename not in filenames:
                assert(filename is None)


def test_runrequest(tempdir):
    runfile_yaml = "%s/yamlsim/run.yaml" % _testdata()
    runfile_json = "%s/yamlsim/run.json" % _testdata()

    for runfile in [runfile_yaml, runfile_json]:
        request = RunRequest(runfile=runfile)
        _test_request(request, tempdir)
