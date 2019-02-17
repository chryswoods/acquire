
import pytest
import datetime
import uuid

from Acquire.ObjectStore import ObjectStore, ObjectStoreError, PAR, \
                                PARError, PARPermissionsError

from Acquire.Service import get_service_account_bucket


@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("simple_objstore")
    return get_service_account_bucket(str(d))


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
