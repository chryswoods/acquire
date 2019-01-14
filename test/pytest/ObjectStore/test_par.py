
import pytest
import datetime
import uuid

from Acquire.ObjectStore import ObjectStore, ObjectStoreError, PAR, PARError, \
                                PARPermissionsError

from Acquire.Service import login_to_service_account


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("simple_objstore")
    return login_to_service_account(str(d))


def test_par(bucket):
    # first try to create a PAR for the whole bucket
    par = ObjectStore.create_par(bucket, readable=False, writeable=True,
                                 duration=100)

    # should not take 10 seconds to create and return the PAR...
    assert(par.seconds_remaining(buffer=0) > 90)
    assert(par.seconds_remaining(buffer=0) < 101)

    # trying to create a par for a non-existant object should fail
    key = "something"
    value = "∆ƒ^ø  ®∆ ®∆ #®∆… ®#€   €"

    with pytest.raises(PARError):
        par = ObjectStore.create_par(bucket, key)

    ObjectStore.set_string_object(bucket, key, value)

    par = ObjectStore.create_par(bucket, key, duration=60)

    assert(par.seconds_remaining(buffer=0) > 55)
    assert(par.seconds_remaining(buffer=0) < 61)

    assert(not par.is_writeable())

    assert(par.key() == key)

    val = par.read().get_string_object()

    assert(val == value)

    value = "∆˚¬#  #ª ƒ∆ ¬¬¬˚¬∂ß ˚¬ ¬¬¬ßßß"

    with pytest.raises(PARPermissionsError):
        par.write().set_string_object(value)

    par = ObjectStore.create_par(bucket, key, readable=True, writeable=True)

    data = par.to_data()
    par2 = PAR.from_data(data)

    value = "something " + str(uuid.uuid4())

    par2.write().set_string_object(value)

    val = par.read().get_string_object()

    assert(val == value)

    par = ObjectStore.create_par(bucket, key, writeable=True, duration=60)

    par.write().set_string_object(value)

    assert(par.read().get_string_object() == value)

    assert(ObjectStore.get_string_object(bucket, key) == value)

    par = ObjectStore.create_par(bucket, readable=False,
                                 writeable=True, duration=120)

    assert(not par.is_readable())
    assert(par.is_writeable())
    assert(par.is_bucket())

    d = "testing"

    keyvals = {"one": "^¬#∆˚¬€", "two": "∆¡πª¨ƒ∆",
               "three": "€√≠ç~ç~€", "four": "hello world!",
               "subdir/five": "#º©√∆˚∆˚¬€ €˚∆ƒ¬"}

    for (key, value) in keyvals.items():
        par.write().set_string_object("%s/%s" % (d, key), value)

    for key in keyvals.keys():
        par = ObjectStore.create_par(bucket, "%s/%s" % (d, key), duration=60)
        value = par.read().get_string_object()

        assert(keyvals[key] == value)


def _test_remote_par():
    remote_par = "https://objectstorage.us-ashburn-1.oraclecloud.com/p/UtFZPuH8gLbOgR_mfa1lim7nf7DTk5qkLGBuvpPwqMU/n/chryswoods/b/testbucket/o/transactions"

    expires_timestamp = datetime.datetime(2020, 1, 1).replace(
            tzinfo=datetime.timezone.utc).timestamp()

    par = PAR(url=remote_par, key="test", is_writeable=True,
              expires_timestamp=expires_timestamp)

    original = par.read().get_string_object()

    value = " ∆∂˚¬´ ƒ€∆® ¬˚∆# ®#®¬∆#˚®∆˚¬#€  #€€€" + str(uuid.uuid4())

    par.write().set_string_object(value)

    val = par.read().get_string_object()

    assert(val != original)

    assert(val == value)

    assert(False)


def _test_remote_bucket_par():
    remote_par = "https://objectstorage.us-ashburn-1.oraclecloud.com/p/YqMRUmCZz6RCJdKlj63zTXQdPj1l7RCJW9bFWy7DxEY/n/chryswoods/b/testbucket/o/"

    expires_timestamp = datetime.datetime(2020, 1, 1).replace(
            tzinfo=datetime.timezone.utc).timestamp()

    par = PAR(url=remote_par, is_readable=False, is_writeable=True,
              expires_timestamp=expires_timestamp)

    key = "this/is/a/test"
    value = "some value " + str(uuid.uuid4())

    par.write().set_string_object(key, value)

    test = par.read().get_string_object(key)

    assert(test == value)

    assert(False)
