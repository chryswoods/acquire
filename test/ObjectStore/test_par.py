
import pytest
import datetime
import uuid

from Acquire.ObjectStore import ObjectStore, ObjectStoreError
from Acquire.Client import PAR, PARError, PARPermissionsError

from Acquire.Service import get_service_account_bucket, \
    push_is_running_service, pop_is_running_service
from Acquire.Crypto import get_private_key


@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("simple_objstore")
    push_is_running_service()
    bucket = get_service_account_bucket(str(d))
    pop_is_running_service()
    return bucket


def test_par(bucket):
    privkey = get_private_key()
    pubkey = privkey.public_key()

    # first try to create a PAR for the whole bucket
    par = ObjectStore.create_par(bucket, readable=False, writeable=True,
                                 duration=100, encrypt_key=pubkey)

    # should not take 10 seconds to create and return the PAR...
    assert(par.seconds_remaining(buffer=0) > 90)
    assert(par.seconds_remaining(buffer=0) < 101)

    # trying to create a par for a non-existant object should fail
    key = "something"
    value = "∆ƒ^ø  ®∆ ®∆ #®∆… ®#€   €"

    with pytest.raises(PARError):
        par = ObjectStore.create_par(bucket, key=key, encrypt_key=pubkey)

    ObjectStore.set_string_object(bucket, key, value)

    par = ObjectStore.create_par(bucket, key=key, duration=60,
                                 encrypt_key=pubkey)

    assert(par.seconds_remaining(buffer=0) > 55)
    assert(par.seconds_remaining(buffer=0) < 61)

    assert(not par.is_writeable())

    assert(par.key() == key)

    val = par.read(privkey).get_string_object()

    assert(val == value)

    value = "∆˚¬#  #ª ƒ∆ ¬¬¬˚¬∂ß ˚¬ ¬¬¬ßßß"

    with pytest.raises(PARPermissionsError):
        par.write(privkey).set_string_object(value)

    par = ObjectStore.create_par(bucket, key=key, readable=True,
                                 writeable=True, encrypt_key=pubkey)

    data = par.to_data()
    par2 = PAR.from_data(data)

    value = "something " + str(uuid.uuid4())

    par2.write(privkey).set_string_object(value)

    val = par.read(privkey).get_string_object()

    assert(val == value)

    par = ObjectStore.create_par(bucket, encrypt_key=pubkey, key=key,
                                 writeable=True, duration=60)

    par.write(privkey).set_string_object(value)

    assert(par.read(privkey).get_string_object() == value)

    assert(ObjectStore.get_string_object(bucket, key) == value)

    par = ObjectStore.create_par(bucket, readable=False,
                                 writeable=True, duration=120,
                                 encrypt_key=pubkey)

    assert(not par.is_readable())
    assert(par.is_writeable())
    assert(par.is_bucket())

    d = "testing"

    keyvals = {"one": "^¬#∆˚¬€", "two": "∆¡πª¨ƒ∆",
               "three": "€√≠ç~ç~€", "four": "hello world!",
               "subdir/five": "#º©√∆˚∆˚¬€ €˚∆ƒ¬"}

    for (key, value) in keyvals.items():
        par.write(privkey).set_string_object("%s/%s" % (d, key), value)

    for key in keyvals.keys():
        par = ObjectStore.create_par(bucket, key="%s/%s" % (d, key),
                                     duration=60, encrypt_key=pubkey)
        value = par.read(privkey).get_string_object()

        assert(keyvals[key] == value)
