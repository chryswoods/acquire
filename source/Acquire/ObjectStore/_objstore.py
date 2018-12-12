
import io as _io
import datetime as _datetime
import uuid as _uuid
import json as _json
import os as _os

from ._errors import ObjectStoreError

__all__ = ["ObjectStore", "set_object_store_backend",
           "use_testing_object_store_backend",
           "use_oci_object_store_backend"]

_objstore_backend = None


def use_testing_object_store_backend(backend):
    from ._testing_objstore import Testing_ObjectStore as _Testing_ObjectStore
    set_object_store_backend(_Testing_ObjectStore)
    return "%s/testing_objstore" % backend


def use_oci_object_store_backend():
    from ._oci_objstore import OCI_ObjectStore as _OCI_ObjectStore
    set_object_store_backend(_OCI_ObjectStore)


class ObjectStore:
    @staticmethod
    def create_bucket(bucket, bucket_name, compartment=None):
        return _objstore_backend.create_bucket(bucket, bucket_name,
                                               compartment)

    @staticmethod
    def get_bucket(bucket, bucket_name, compartment=None,
                   create_if_needed=True):
        return _objstore_backend.get_bucket(bucket, bucket_name,
                                            compartment, create_if_needed)

    @staticmethod
    def get_object_as_file(bucket, key, filename):
        return _objstore_backend.get_object_as_file(bucket, key, filename)

    @staticmethod
    def get_object(bucket, key):
        return _objstore_backend.get_object(bucket, key)

    @staticmethod
    def get_string_object(bucket, key):
        return _objstore_backend.get_string_object(bucket, key)

    @staticmethod
    def get_object_from_json(bucket, key):
        return _objstore_backend.get_object_from_json(bucket, key)

    @staticmethod
    def get_all_object_names(bucket, prefix=None):
        return _objstore_backend.get_all_object_names(bucket, prefix)

    @staticmethod
    def get_all_objects(bucket, prefix=None):
        return _objstore_backend.get_all_objects(bucket, prefix)

    @staticmethod
    def get_all_strings(bucket, prefix=None):
        return _objstore_backend.get_all_strings(bucket, prefix)

    @staticmethod
    def set_object(bucket, key, data):
        _objstore_backend.set_object(bucket, key, data)

    @staticmethod
    def set_object_from_file(bucket, key, filename):
        _objstore_backend.set_object_from_file(bucket, key, filename)

    @staticmethod
    def set_string_object(bucket, key, string_data):
        _objstore_backend.set_string_object(bucket, key, string_data)

    @staticmethod
    def set_object_from_json(bucket, key, data):
        _objstore_backend.set_object_from_json(bucket, key, data)

    @staticmethod
    def log(bucket, message, prefix="log"):
        _objstore_backend.log(bucket, message, prefix)

    @staticmethod
    def delete_all_objects(bucket, prefix=None):
        _objstore_backend.delete_all_objects(bucket, prefix)

    @staticmethod
    def get_log(bucket, log="log"):
        _objstore_backend.get_log(bucket, log)

    @staticmethod
    def clear_log(bucket, log="log"):
        _objstore_backend.clear_log(bucket, log)

    @staticmethod
    def delete_object(bucket, key):
        _objstore_backend.delete_object(bucket, key)

    @staticmethod
    def clear_all_except(bucket, keys):
        _objstore_backend.clear_all_except(bucket, keys)


def set_object_store_backend(backend):
    """Set the backend that is used to actually connect to
       the object store. This can only be set once in the program!
    """
    global _objstore_backend

    if backend == _objstore_backend:
        return

    if _objstore_backend is not None:
        raise ObjectStoreError("You cannot change the object store "
                               "backend once it has been already set!")

    _objstore_backend = backend
