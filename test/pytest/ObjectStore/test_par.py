import pytest

import datetime

from Acquire.ObjectStore import ObjectStore, ObjectStoreError, PAR, PARError
from Acquire.Service import login_to_service_account


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("simple_objstore")
    return login_to_service_account(str(d))


def test_par(bucket):
    # first try to create a PAR for the whole bucket
    par = ObjectStore.create_par(bucket, writeable=False, duration=100)

    # should not take 10 seconds to create and return the PAR...
    assert(par.seconds_remaining() > 90)
    assert(par.seconds_remaining() < 101)

    # trying to create a par for a non-existant object should fail
    key = "something"
    value = "∆ƒ^ø  ®∆ ®∆ #®∆… ®#€   €"

    with pytest.raises(PARError):
        par = ObjectStore.create_par(bucket, key)

    ObjectStore.set_string_object(bucket, key, value)

    par = ObjectStore.create_par(bucket, key)

    assert(par.seconds_remaining() > 3590)
    assert(par.seconds_remaining() < 3601)

    assert(not par.is_writeable())

    assert(par.key() == key)
