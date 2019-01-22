
import os as _os
import shutil as _shutil
import datetime as _datetime
import uuid as _uuid
import json as _json
import glob as _glob
import threading
import uuid as _uuid

from ._par import PAR as _PAR
from ._encoding import get_datetime_now as _get_datetime_now
from ._encoding import datetime_to_string as _datetime_to_string
from ._encoding import string_to_datetime as _string_to_datetime

from ._errors import ObjectStoreError, PARError

_rlock = threading.RLock()

__all__ = ["Testing_ObjectStore"]


class Testing_ObjectStore:
    """This is a dummy object store that writes objects to
       the standard posix filesystem when running tests
    """
    @staticmethod
    def create_bucket(bucket, bucket_name, compartment=None):
        """Create and return a new bucket in the object store called
           'bucket_name', optionally placing it into the compartment
           identified by 'compartment'. This will raise an
           ObjectStoreError if this bucket already exists
        """
        bucket_name = str(bucket_name)

        if compartment is not None:
            if compartment.endswith("/"):
                bucket = compartment
            else:
                bucket = "%s/" % compartment

        full_name = _os.path.join(_os.path.split(bucket)[0], bucket_name)

        if _os.path.exists(full_name):
            raise ObjectStoreError(
                "CANNOT CREATE NEW BUCKET '%s': EXISTS!" % bucket_name)

        _os.makedirs(full_name)

        return full_name

    @staticmethod
    def get_bucket(bucket, bucket_name, compartment=None,
                   create_if_needed=True):
        """Find and return a new bucket in the object store called
           'bucket_name', optionally placing it into the compartment
           identified by 'compartment'. If 'create_if_needed' is True
           then the bucket will be created if it doesn't exist. Otherwise,
           if the bucket does not exist then an exception will be raised.
        """
        bucket_name = str(bucket_name)

        if compartment is not None:
            if compartment.endswith("/"):
                bucket = compartment
            else:
                bucket = "%s/" % compartment

        full_name = _os.path.join(_os.path.split(bucket)[0], bucket_name)

        if not _os.path.exists(full_name):
            if create_if_needed:
                _os.makedirs(full_name)
            else:
                raise ObjectStoreError(
                    "There is no bucket available called '%s' in "
                    "compartment '%s'" % (bucket_name, compartment))

        return full_name

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
        if key is not None:
            if not _os.path.exists("%s/%s._data" % (bucket, key)):
                raise PARError(
                    "The object '%s' in bucket '%s' does not exist!" %
                    (key, bucket))
        elif not _os.path.exists(bucket):
            raise PARError("The bucket '%s' does not exist!" % bucket)

        url = "file://%s" % bucket

        if key:
            url = "%s/%s" % (url, key)

        # get the time this PAR was created
        created_datetime = _get_datetime_now()

        # get the UTC datetime when this PAR should expire
        expires_datetime = created_datetime + \
            _datetime.timedelta(seconds=duration)

        # mimic limitations of OCI - cannot have a bucket PAR with
        # read permissions!
        if (key is None) and readable:
            raise PARError(
                "You cannot create a Bucket PAR that has read permissions "
                "due to a limitation in the underlying platform")

        return _PAR(url=url, key=key,
                    created_datetime=created_datetime,
                    expires_datetime=expires_datetime,
                    is_readable=readable, is_writeable=writeable,
                    par_id=str(_uuid.uuid4()),
                    driver="testing_objstore")

    @staticmethod
    def get_object_as_file(bucket, key, filename):
        """Get the object contained in the key 'key' in the passed 'bucket'
           and writing this to the file called 'filename'"""

        if not _os.path.exists("%s/%s._data" % (bucket, key)):
            raise ObjectStoreError("No object at key '%s'" % key)

        _shutil.copy("%s/%s._data" % (bucket, key), filename)

    @staticmethod
    def get_object(bucket, key):
        """Return the binary data contained in the key 'key' in the
           passed bucket"""

        with _rlock:
            if _os.path.exists("%s/%s._data" % (bucket, key)):
                return open("%s/%s._data" % (bucket, key), "rb").read()
            else:
                raise ObjectStoreError("No object at key '%s'" % key)

    @staticmethod
    def get_string_object(bucket, key):
        """Return the string in 'bucket' associated with 'key'"""
        return Testing_ObjectStore.get_object(bucket, key).decode("utf-8")

    @staticmethod
    def get_object_from_json(bucket, key):
        """Return an object constructed from json stored at 'key' in
           the passed bucket. This returns None if there is no data
           at this key
        """

        data = None

        try:
            data = Testing_ObjectStore.get_string_object(bucket, key)
        except:
            return None

        return _json.loads(data)

    @staticmethod
    def get_all_object_names(bucket, prefix=None):
        """Returns the names of all objects in the passed bucket"""

        if prefix:
            parts = prefix.split("/")
            root = "%s/%s/" % (bucket, "/".join(parts[0:-1]))
            prefix = parts[-1]
        else:
            root = "%s/" % bucket
            prefix = None

        names = [_os.path.join(dp, f) for dp, dn, filenames in
                 _os.walk(root) for f in filenames
                 if _os.path.splitext(f)[1] == '._data']

        object_names = []
        for name in names:
            try:
                name = name[0:-6].split(root)[1]
                if prefix is None:
                    object_names.append(name)
                elif name.startswith(prefix):
                    object_names.append(name[len(prefix):])
            except:
                raise IndexError("Cannot extract from name: Root = %s, "
                                 "name = %s" % (root, name[0:-6]))

        return object_names

    @staticmethod
    def get_all_objects(bucket, prefix=None):
        """Return all of the objects in the passed bucket"""

        objects = {}
        names = Testing_ObjectStore.get_all_object_names(bucket, prefix)

        if prefix:
            for name in names:
                objects[name] = Testing_ObjectStore.get_object(
                                    bucket, "%s/%s" % (prefix, name))
        else:
            for name in names:
                objects[name] = Testing_ObjectStore.get_object(bucket, name)

        return objects

    @staticmethod
    def get_all_strings(bucket, prefix=None):
        """Return all of the strings in the passed bucket"""

        objects = Testing_ObjectStore.get_all_objects(bucket, prefix)

        names = list(objects.keys())

        for name in names:
            try:
                s = objects[name].decode("utf-8")
                objects[name] = s
            except:
                del objects[name]

        return objects

    @staticmethod
    def set_object(bucket, key, data):
        """Set the value of 'key' in 'bucket' to binary 'data'"""

        filename = "%s/%s._data" % (bucket, key)

        with _rlock:
            try:
                with open(filename, 'wb') as FILE:
                    FILE.write(data)
                    FILE.flush()
            except:
                dir = "/".join(filename.split("/")[0:-1])
                _os.makedirs(dir, exist_ok=True)
                with open(filename, 'wb') as FILE:
                    FILE.write(data)
                    FILE.flush()

    @staticmethod
    def set_object_from_file(bucket, key, filename):
        """Set the value of 'key' in 'bucket' to equal the contents
           of the file located by 'filename'"""

        Testing_ObjectStore.set_object(bucket, key,
                                       open(filename, 'rb').read())

    @staticmethod
    def set_string_object(bucket, key, string_data):
        """Set the value of 'key' in 'bucket' to the string 'string_data'"""
        Testing_ObjectStore.set_object(bucket, key,
                                       string_data.encode("utf-8"))

    @staticmethod
    def set_object_from_json(bucket, key, data):
        """Set the value of 'key' in 'bucket' to equal to contents
           of 'data', which has been encoded to json"""
        Testing_ObjectStore.set_string_object(bucket, key, _json.dumps(data))

    @staticmethod
    def delete_all_objects(bucket, prefix=None):
        """Deletes all objects..."""
        if prefix:
            _shutil.rmtree("%s/%s" % (bucket, prefix), ignore_errors=True)
        else:
            _shutil.rmtree(bucket, ignore_errors=True)

    @staticmethod
    def delete_object(bucket, key):
        """Removes the object at 'key'"""
        try:
            _os.remove("%s/%s._data" % (bucket, key))
        except:
            pass

    @staticmethod
    def clear_all_except(bucket, keys):
        """Removes all objects from the passed 'bucket' except those
           whose keys are or start with any key in 'keys'"""

        names = Testing_ObjectStore.get_all_object_names(bucket)

        for name in names:
            remove = True

            for key in keys:
                if name.startswith(key):
                    remove = False
                    break

            if remove:
                Testing_ObjectStore.delete_object(bucket, key)
