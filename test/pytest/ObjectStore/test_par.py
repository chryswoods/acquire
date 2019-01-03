
import pytest
import datetime

from Acquire.ObjectStore import ObjectStore, ObjectStoreError, PAR, PARError, \
                                PARPermissionsError

from Acquire.Service import login_to_service_account


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("simple_objstore")
    return login_to_service_account(str(d))


def test_par(bucket):
    # first try to create a PAR for the whole bucket
    par = ObjectStore.create_par(bucket, writeable=False, duration=100)

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

    par = ObjectStore.create_par(bucket, key, writeable=True, duration=60)

    par.write().set_string_object(value)

    assert(par.read().get_string_object() == value)

    assert(ObjectStore.get_string_object(bucket, key) == value)

    par = ObjectStore.create_par(bucket, writeable=True, duration=120)

    assert(par.is_writeable())
    assert(par.is_bucket())

    d = "testing"

    keyvals = {"one": "^¬#∆˚¬€", "two": "∆¡πª¨ƒ∆",
               "three": "€√≠ç~ç~€", "four": "hello world!",
               "subdir/five": "#º©√∆˚∆˚¬€ €˚∆ƒ¬"}

    writer = par.write()
    reader = par.read()

    for (key, value) in keyvals.items():
        fullkey = "%s/%s" % (d, key)
        writer.set_string_object(fullkey, value)

        assert(reader.get_string_object(fullkey) == value)

    objnames = reader.get_all_object_names(d)
    objs = writer.get_all_strings(d)

    for (key, value) in keyvals.items():
        assert(key in objnames)
        assert(objs[key] == value)


def test_remote_par():
    remote_par = "https://objectstorage.us-ashburn-1.oraclecloud.com/p/UtFZPuH8gLbOgR_mfa1lim7nf7DTk5qkLGBuvpPwqMU/n/chryswoods/b/testbucket/o/transactions"

    expires_timestamp = datetime.datetime(2020,1,1).replace(
            tzinfo=datetime.timezone.utc).timestamp()

    par = PAR(url=remote_par, key="test", is_writeable=True,
              expires_timestamp=expires_timestamp)

    data = par.read().get_string_object()

    value = "∆^∆ƒ^ø∆  ∆^ø∑∆ ƒ ∆^ø∑øøø"

    par.write().set_string_object(value)

    val = par.read().get_string_object()

    assert(val == value)

    assert(False)
