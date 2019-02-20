
import io as _io
import datetime as _datetime
import uuid as _uuid
import json as _json
import os as _os

__all__ = ["ObjectStore", "set_object_store_backend",
           "use_testing_object_store_backend",
           "use_oci_object_store_backend"]

_objstore_backend = None


def use_testing_object_store_backend(backend):
    from ._testing_objstore import Testing_ObjectStore as _Testing_ObjectStore
    set_object_store_backend(_Testing_ObjectStore)
    bucket = "%s/testing_objstore" % backend

    try:
        # make sure that this directory exists if it doesn't already
        _os.mkdir(bucket)
    except:
        pass

    return bucket


def use_oci_object_store_backend():
    from ._oci_objstore import OCI_ObjectStore as _OCI_ObjectStore
    set_object_store_backend(_OCI_ObjectStore)


class ObjectStore:
    @staticmethod
    def create_bucket(bucket, bucket_name, compartment=None):
        """Create and return a new bucket in the object store called
           'bucket_name', optionally placing it into the compartment
           identified by 'compartment'. This will raise an
           ObjectStoreError if this bucket already exists
        """
        return _objstore_backend.create_bucket(bucket, bucket_name,
                                               compartment)

    @staticmethod
    def get_bucket(bucket, bucket_name, compartment=None,
                   create_if_needed=True):
        """Find and return a new bucket in the object store called
           'bucket_name', optionally placing it into the compartment
           identified by 'compartment'. If 'create_if_needed' is True
           then the bucket will be created if it doesn't exist. Otherwise,
           if the bucket does not exist then an exception will be raised.
        """
        return _objstore_backend.get_bucket(bucket, bucket_name,
                                            compartment, create_if_needed)

    @staticmethod
    def create_par(bucket, key=None, readable=True,
                   writeable=False, duration=3600):
        """Create a pre-authenticated request for the passed bucket and
           key (if key is None then the request is for the entire bucket).
           This will return a PAR object that will contain a URL that can
           be used to access the object/bucket. If writeable is true, then
           the URL will also allow the object/bucket to be written to.
           PARs are time-limited. Set the lifetime in seconds by passing
           in 'duration' (by default this is one hour)
        """
        from Acquire.ObjectStore import PAR as _PAR

        par = _objstore_backend.create_par(bucket, key, readable,
                                           writeable, duration)

        if not isinstance(par, _PAR):
            raise TypeError("A create_par request should always return an "
                            "value of type PAR: %s is not correct!" % par)

        return par

    @staticmethod
    def get_object_as_file(bucket, key, filename):
        """Get the object contained in the key 'key' in the passed 'bucket'
           and writing this to the file called 'filename'"""
        return _objstore_backend.get_object_as_file(bucket, key, filename)

    @staticmethod
    def get_object(bucket, key):
        """Return the binary data contained in the key 'key' in the
           passed bucket"""
        return _objstore_backend.get_object(bucket, key)

    @staticmethod
    def get_string_object(bucket, key):
        """Return the string in 'bucket' associated with 'key'"""
        return _objstore_backend.get_string_object(bucket, key)

    @staticmethod
    def get_object_from_json(bucket, key):
        """Return an object constructed from json stored at 'key' in
           the passed bucket. This returns None if there is no data
           at this key
        """
        return _objstore_backend.get_object_from_json(bucket, key)

    @staticmethod
    def get_all_object_names(bucket, prefix=None):
        """Returns the names of all objects in the passed bucket"""
        return _objstore_backend.get_all_object_names(bucket, prefix)

    @staticmethod
    def get_all_objects(bucket, prefix=None):
        """Return all of the objects in the passed bucket"""
        return _objstore_backend.get_all_objects(bucket, prefix)

    @staticmethod
    def get_all_strings(bucket, prefix=None):
        """Return all of the strings in the passed bucket"""
        return _objstore_backend.get_all_strings(bucket, prefix)

    @staticmethod
    def set_object(bucket, key, data):
        """Set the value of 'key' in 'bucket' to binary 'data'"""
        _objstore_backend.set_object(bucket, key, data)

    @staticmethod
    def set_object_from_file(bucket, key, filename):
        """Set the value of 'key' in 'bucket' to equal the contents
           of the file located by 'filename'"""
        _objstore_backend.set_object_from_file(bucket, key, filename)

    @staticmethod
    def set_string_object(bucket, key, string_data):
        """Set the value of 'key' in 'bucket' to the string 'string_data'"""
        _objstore_backend.set_string_object(bucket, key, string_data)

    @staticmethod
    def set_object_from_json(bucket, key, data):
        """Set the value of 'key' in 'bucket' to equal to contents
           of 'data', which has been encoded to json"""
        _objstore_backend.set_object_from_json(bucket, key, data)

    @staticmethod
    def delete_all_objects(bucket, prefix=None):
        """Deletes all objects..."""
        _objstore_backend.delete_all_objects(bucket, prefix)

    @staticmethod
    def delete_object(bucket, key):
        """Removes the object at 'key'"""
        _objstore_backend.delete_object(bucket, key)

    @staticmethod
    def clear_all_except(bucket, keys):
        """Removes all objects from the passed 'bucket' except those
           whose keys are or start with any key in 'keys'"""
        _objstore_backend.clear_all_except(bucket, keys)


def set_object_store_backend(backend):
    """Set the backend that is used to actually connect to
       the object store. This can only be set once in the program!
    """
    global _objstore_backend

    if backend == _objstore_backend:
        return

    if _objstore_backend is not None:
        from Acquire.ObjectStore import ObjectStoreError
        raise ObjectStoreError("You cannot change the object store "
                               "backend once it has been already set!")

    _objstore_backend = backend
