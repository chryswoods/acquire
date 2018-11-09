
import pytest

# Testing mode is switched on using this environment variable.
# This tells Acquire not to try to log into the cloud, but to
# instead create and use a fake object store locally
import os

from Acquire.ObjectStore import ObjectStore, ObjectStoreError
from Acquire.Service import login_to_service_account


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("simple_objstore")
    return login_to_service_account(str(d))


def test_objstore(bucket):
    keys = []

    message = "ƒƒƒ Hello World ∂∂∂"

    ObjectStore.set_string_object(bucket, "test", message)
    keys.append("test")

    assert(message == ObjectStore.get_string_object(bucket, "test"))

    message = "€€#¢∞ Hello ˚ƒ´πµçµΩ"

    ObjectStore.set_string_object(bucket, "test/something", message)
    keys.append("test/something")

    assert(message == ObjectStore.get_string_object(bucket, "test/something"))

    data = {"cat": "mieow",
            "dog": "woof",
            "sounds": [1, 2, 3, 4, 5],
            "flag": True}

    ObjectStore.set_object_from_json(bucket, "test/object", data)
    keys.append("test/object")

    assert(data == ObjectStore.get_object_from_json(bucket, "test/object"))

    names = ObjectStore.get_all_object_names(bucket)

    assert(len(names) == len(keys))

    for name in names:
        assert(name in keys)

    new_bucket = ObjectStore.create_bucket(bucket, "new_bucket")

    ObjectStore.set_object_from_json(new_bucket, "test/object2", data)
    assert(data == ObjectStore.get_object_from_json(new_bucket,
                                                    "test/object2"))

    with pytest.raises(ObjectStoreError):
        new_bucket = ObjectStore.create_bucket(bucket, "testing_objstore")

    with pytest.raises(ObjectStoreError):
        new_bucket = ObjectStore.create_bucket(bucket, "new_bucket")
