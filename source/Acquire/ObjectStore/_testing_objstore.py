
import os as _os
import shutil as _shutil
import datetime as _datetime
import uuid as _uuid
import json as _json
import glob as _glob
import threading

from ._errors import ObjectStoreError

_rlock = threading.RLock()

__all__ = ["Testing_ObjectStore"]


class Testing_ObjectStore:
    """This is a dummy object store that writes objects to
       the standard posix filesystem when running tests
    """

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
            root = "%s/%s/" % (bucket, prefix)
        else:
            root = "%s/" % bucket

        names = [_os.path.join(dp, f) for dp, dn, filenames in
                 _os.walk(root) for f in filenames
                 if _os.path.splitext(f)[1] == '._data']

        object_names = []
        for name in names:
            try:
                object_names.append(name[0:-6].split(root)[1])
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
    def log(bucket, message, prefix="log"):
        """Log the the passed message to the object store in
           the bucket with key "key/timestamp" (defaults
           to "log/timestamp"
        """

        Testing_ObjectStore.set_string_object(
            bucket, "%s/%s" % (
                prefix, _datetime.datetime.utcnow().timestamp()), str(message))

    @staticmethod
    def delete_all_objects(bucket, prefix=None):
        """Deletes all objects..."""
        if prefix:
            _shutil.rmtree("%s/%s" % (bucket, prefix), ignore_errors=True)
        else:
            _shutil.rmtree(bucket, ignore_errors=True)

    @staticmethod
    def get_log(bucket, log="log"):
        """Return the complete log as an xml string"""
        objs = Testing_ObjectStore.get_all_strings(bucket, log)

        lines = []
        lines.append("<log>")

        timestamps = list(objs.keys())
        timestamps.sort()

        for timestamp in timestamps:
            lines.append("<logitem>")
            lines.append("<timestamp>%s</timestamp>" %
                         _datetime.datetime.fromtimestamp(float(timestamp)))
            lines.append("<message>%s</message>" % objs[timestamp])
            lines.append("</logitem>")

        lines.append("</log>")

        return "".join(lines)

    @staticmethod
    def clear_log(bucket, log="log"):
        """Clears out the log"""
        Testing_ObjectStore.delete_all_objects(bucket, log)

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
