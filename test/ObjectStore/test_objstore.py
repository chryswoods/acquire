
import pytest

from Acquire.ObjectStore import ObjectStore, ObjectStoreError
from Acquire.Service import get_service_account_bucket, \
    push_is_running_service, pop_is_running_service, \
    is_running_service


@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("simple_objstore")
    push_is_running_service()
    bucket = get_service_account_bucket(str(d))

    while is_running_service():
        pop_is_running_service()

    return bucket


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

    names = ObjectStore.get_all_object_names(bucket, "test")

    assert(len(names) == 3)

    names = ObjectStore.get_all_object_names(bucket, "test/")

    assert(len(names) == 2)

    names = ObjectStore.get_all_object_names(bucket, "test/some")

    assert(len(names) == 1)

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

    with pytest.raises(ObjectStoreError):
        new_bucket = ObjectStore.get_bucket(bucket, "get_bucket",
                                            create_if_needed=False)

    new_bucket = ObjectStore.get_bucket(bucket, "get_bucket",
                                        create_if_needed=True)

    test_key = "test_string"
    test_value = "test_string_value"

    ObjectStore.set_string_object(new_bucket, test_key, test_value)

    new_bucket2 = ObjectStore.get_bucket(bucket, "get_bucket",
                                         create_if_needed=False)

    test_value2 = ObjectStore.get_string_object(new_bucket2, test_key)

    assert(test_value == test_value2)
