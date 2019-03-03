
import datetime as _datetime
import json as _json
import os as _os

__all__ = ["PAR", "BucketReader", "BucketWriter", "ObjectReader",
           "ObjectWriter"]


class PAR:
    """This class holds the result of a pre-authenticated request
       (a PAR - also called a pre-signed request). This holds a URL
       at which an object (or entire bucket) in the object store
       can be accessed. The PAR has a lifetime.

       This object can safely be saved and/or transmitted from
       the server to the client
    """
    def __init__(self, url=None, key=None,
                 created_datetime=None,
                 expires_datetime=None,
                 is_readable=True,
                 is_writeable=False,
                 par_id=None, par_name=None,
                 driver=None):
        """Construct a PAR result by passing in the URL at which the
           object can be accessed, the UTC datetime when this expires,
           whether this is writeable, and (optionally) 'key' for the
           object that is accessed (if this is not supplied then an
           entire bucket is accessed). If 'is_readable', then read-access
           has been granted, while if 'is_writeable' then write
           access has been granted. Otherwise no access is possible.
           This also records the type of object store behind this PAR
           in the free-form string 'driver'. You can optionally supply
           the ID of the PAR by passing in 'par_id', the user-supplied name,
           of the PAR by passing in 'par_name', and the time it
           was created using 'created_datetime' (in the same format
           as 'expires_datetime' - should be a UTC datetime with UTC tzinfo)
        """
        self._url = url
        self._key = key
        self._created_datetime = created_datetime
        self._expires_datetime = expires_datetime
        self._driver = driver
        self._par_id = par_id
        self._par_name = par_name

        if is_readable:
            self._is_readable = True
        else:
            self._is_readable = False

        if is_writeable:
            self._is_writeable = True
        else:
            self._is_writeable = False

        if not (self._is_readable or self._is_writeable):
            from Acquire.ObjectStore import PARPermissionsError
            raise PARPermissionsError(
                "You cannot create a PAR that has no read or write "
                "permissions!")

    def __str__(self):
        try:
            my_url = self.url()
        except:
            return "PAR( expired )"

        if self._key is None:
            return "PAR( bucket=True, url=%s, seconds_remaining=%s )" % \
                (my_url, self.seconds_remaining(buffer=0))
        else:
            return "PAR( key=%s, url=%s, seconds_remaining=%s )" % \
                (self.key(), my_url, self.seconds_remaining(buffer=0))

    def url(self):
        """Return the URL at which the bucket/object can be accessed. This
           will raise a PARTimeoutError if the url has less than 30 seconds
           of validity left"""
        if self.seconds_remaining(buffer=30) <= 0:
            from Acquire.ObjectStore import PARTimeoutError
            raise PARTimeoutError(
                "The URL behind this PAR has expired and is no longer valid")

        return self._url

    def par_id(self):
        """Return the ID of the PAR, if this was supplied by the underlying
           driver. This could be useful for PAR management by the server
        """
        return self._par_id

    def par_name(self):
        """Return the user-supplied name of the PAR, if this was supplied
           by the user and supported by the underlying driver. This could
           be useful for PAR management by the server
        """
        return self._par_name

    def is_readable(self):
        """Return whether or not this PAR gives read access"""
        return self._is_readable

    def is_writeable(self):
        """Return whether or not this PAR gives write access"""
        return self._is_writeable

    def key(self):
        """Return the key for the object this accesses - this is None
           if the PAR grants access to the entire bucket"""
        return self._key

    def is_bucket(self):
        """Return whether or not this PAR is for an entire bucket"""
        return self._key is None

    def is_object(self):
        """Return whether or not this PAR is for a single object"""
        return self._key is not None

    def driver(self):
        """Return the underlying object store driver used for this PAR"""
        return self._driver

    def seconds_remaining(self, buffer=30):
        """Return the number of seconds remaining before this PAR expires.
           This will return 0 if the PAR has already expired. To be safe,
           you should renew PARs if the number of seconds remaining is less
           than 60. This will subtract 'buffer' seconds from the actual
           validity to provide a buffer against race conditions (function
           says this is valid when it is not)
        """
        from Acquire.ObjectStore import get_datetime_now as _get_datetime_now
        now = _get_datetime_now()

        buffer = float(buffer)

        if buffer < 0:
            buffer = 0

        delta = (self._expires_datetime - now).total_seconds() - buffer

        if delta < 0:
            return 0
        else:
            return delta

    def read(self):
        """Return an object that can be used to read data from this PAR"""
        if not self.is_readable():
            from Acquire.ObjectStore import PARPermissionsError
            raise PARPermissionsError(
                "You do not have permission to read from this PAR: %s" % self)

        if self.is_bucket():
            return BucketReader(self)
        else:
            return ObjectReader(self)

    def write(self):
        """Return an object that can be used to write data to this PAR"""
        if not self.is_writeable():
            from Acquire.ObjectStore import PARPermissionsError
            raise PARPermissionsError(
                "You do not have permission to write to this PAR: %s" % self)

        if self.is_bucket():
            return BucketWriter(self)
        else:
            return ObjectWriter(self)

    def to_data(self):
        """Return a json-serialisable dictionary that contains all data
           for this object
        """
        data = {}

        from Acquire.ObjectStore import datetime_to_string \
            as _datetime_to_string

        data["url"] = self._url
        data["key"] = self._key
        data["created_datetime"] = _datetime_to_string(self._created_datetime)
        data["expires_datetime"] = _datetime_to_string(self._expires_datetime)
        data["driver"] = self._driver
        data["par_id"] = self._par_id
        data["par_name"] = self._par_name
        data["is_readable"] = self._is_readable
        data["is_writeable"] = self._is_writeable

        return data

    @staticmethod
    def from_data(data):
        """Return a PAR constructed from the passed json-deserliased
           dictionary
        """
        if data is None or len(data) == 0:
            return None

        from Acquire.ObjectStore import string_to_datetime \
            as _string_to_datetime

        par = PAR()

        par._url = data["url"]

        if par._url is not None:
            par._url = str(par._url)

        par._key = data["key"]

        if par._key is not None:
            par._key = str(par._key)

        par._created_datetime = _string_to_datetime(data["created_datetime"])
        par._expires_datetime = _string_to_datetime(data["expires_datetime"])
        par._driver = data["driver"]
        par._par_id = data["par_id"]
        par._par_name = data["par_name"]
        par._is_readable = data["is_readable"]
        par._is_writeable = data["is_writeable"]

        return par


def _url_to_filepath(url):
    """Internal function used to strip the "file://" from the beginning
       of a file url
    """
    return url[7:]


def _read_local(url):
    """Internal function used to read data from the local testing object
       store
    """
    with open("%s._data" % _url_to_filepath(url), "rb") as FILE:
        return FILE.read()


def _read_remote(url):
    """Internal function used to read data from a remote URL"""
    status_code = None
    response = None

    try:
        from Acquire.Stubs import requests as _requests
        response = _requests.get(url)
        status_code = response.status_code
    except Exception as e:
        from Acquire.ObjectStore import PARReadError
        raise PARReadError(
            "Cannot read the remote PAR URL '%s' because of a possible "
            "nework issue: %s" % (url, str(e)))

    output = response.content

    if status_code != 200:
        from Acquire.ObjectStore import PARReadError
        raise PARReadError(
            "Failed to read data from the PAR URL. HTTP status code = %s, "
            "returned output: %s" % (status_code, output))

    return output


def _list_local(url):
    """Internal function to list all of the objects keys below 'url'"""
    local_dir = _url_to_filepath(url)

    keys = []

    for dirpath, _, filenames in _os.walk(local_dir):
        local_path = dirpath[len(local_dir):]
        has_local_path = (len(local_path) > 0)

        for filename in filenames:
            if filename.endswith("._data"):
                filename = filename[0:-6]

                if has_local_path:
                    keys.append("%s/%s" % (local_path, filename))
                else:
                    keys.append(filename)

    return keys


def _list_remote(url):
    """Internal function to list all of the objects keys below 'url'"""
    return []


def _write_local(url, data):
    """Internal function used to write data to a local file"""
    filename = "%s._data" % _url_to_filepath(url)

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


def _write_remote(url, data):
    """Internal function used to write data to the passed remote URL"""
    try:
        from Acquire.Stubs import requests as _requests
        response = _requests.put(url, data=data)
        status_code = response.status_code
    except Exception as e:
        from Acquire.ObjectStore import PARWriteError
        raise PARWriteError(
            "Cannot write data to the remote PAR URL '%s' because of a "
            "possible nework issue: %s" % (url, str(e)))

    if status_code != 200:
        from Acquire.ObjectStore import PARWriteError
        raise PARWriteError(
            "Cannot write data to the remote PAR URL '%s' because of a "
            "possible nework issue: %s" % (url, str(response.content)))


def _join_bucket_and_prefix(url, prefix):
    """Join together the passed url and prefix, returning the
       url directory and the remainig part which is the start
       of the file name
    """
    if prefix is None:
        return url

    parts = prefix.split("/")

    return ("%s/%s" % (url, "/".join(parts[0:-2])), parts[-1])


class BucketReader:
    """This class provides functions to enable reading data from a
       bucket via a PAR
    """
    def __init__(self, par=None):
        if par:
            if not isinstance(par, PAR):
                raise TypeError(
                    "You can only create a BucketReader from a PAR")
            elif not par.is_bucket():
                raise ValueError(
                    "You can only create a BucketReader from a PAR that "
                    "represents an entire bucket: %s" % par)
            elif not par.is_readable():
                from Acquire.ObjectStore import PARPermissionsError
                raise PARPermissionsError(
                    "You cannot create a BucketReader from a PAR without "
                    "read permissions: %s" % par)

            self._par = par
        else:
            self._par = None

    def get_object(self, key):
        """Return the binary data contained in the key 'key' in the
           passed bucket"""
        if self._par is None:
            from Acquire.ObjectStore import PARError
            raise PARError("You cannot read data from an empty PAR")

        while key.startswith("/"):
            key = key[1:]

        url = self._par.url()

        if url.endswith("/"):
            url = "%s%s" % (url, key)
        else:
            url = "%s/%s" % (url, key)

        if url.startswith("file://"):
            return _read_local(url)
        else:
            return _read_remote(url)

    def get_object_as_file(self, key, filename):
        """Get the object contained in the key 'key' in the passed 'bucket'
           and writing this to the file called 'filename'"""
        objdata = self.get_object(key)

        with open(filename, "wb") as FILE:
            FILE.write(objdata)

    def get_string_object(self, key):
        """Return the string in 'bucket' associated with 'key'"""
        data = self.get_object(key)

        try:
            return data.decode("utf-8")
        except Exception as e:
            raise TypeError(
                "The object behind this PAR cannot be converted to a string. "
                "Error is: %s" % str(e))

    def get_object_from_json(self, key):
        """Return an object constructed from json stored at 'key' in
           the passed bucket. This raises an exception if there is no
           data or the PAR has expired
        """
        data = self.get_string_object(key)
        return _json.loads(data)

    def get_all_object_names(self, prefix=None):
        """Returns the names of all objects in the passed bucket"""
        (url, part) = _join_bucket_and_prefix(self._par.url(), prefix)

        if url.startswith("file://"):
            objnames = _list_local(url)
        else:
            objnames = _list_remote(url)

        # scan the object names returned and discard the ones that don't
        # match the prefix
        matches = []

        if len(part) > 0:
            for objname in objnames:
                if objname.startswith(part):
                    objname = objname[len(part):]

                    while objname.startswith("/"):
                        objname = objname[1:]

                    matches.append(objname)
        else:
            matches = objnames

        return matches

    def get_all_objects(self, prefix=None):
        """Return all of the objects in the passed bucket"""
        names = self.get_all_object_names(prefix)

        objects = {}

        if prefix:
            for name in names:
                objects[name] = self.get_object(
                                    "%s/%s" % (prefix, name))
        else:
            for name in names:
                objects[name] = self.get_object(name)

        return objects

    def get_all_strings(self, prefix=None):
        """Return all of the strings in the passed bucket"""
        objects = self.get_all_objects(prefix)

        names = list(objects.keys())

        for name in names:
            try:
                s = objects[name].decode("utf-8")
                objects[name] = s
            except:
                del objects[name]

        return objects


class BucketWriter:
    """This class provides functions to enable writing data to a
       bucket via a PAR
    """
    def __init__(self, par):
        if par:
            if not isinstance(par, PAR):
                raise TypeError(
                    "You can only create a BucketReader from a PAR")
            elif not par.is_bucket():
                raise ValueError(
                    "You can only create a BucketReader from a PAR that "
                    "represents an entire bucket: %s" % par)
            elif not par.is_writeable():
                from Acquire.ObjectStore import PARPermissionsError
                raise PARPermissionsError(
                    "You cannot create a BucketWriter from a PAR without "
                    "write permissions: %s" % par)

            self._par = par
        else:
            self._par = None

    def set_object(self, key, data):
        """Set the value of 'key' in 'bucket' to binary 'data'"""
        if self._par is None:
            from Acquire.ObjectStore import PARError
            raise PARError("You cannot write data to an empty PAR")

        while key.startswith("/"):
            key = key[1:]

        url = self._par.url()

        if url.endswith("/"):
            url = "%s%s" % (url, key)
        else:
            url = "%s/%s" % (url, key)

        if url.startswith("file://"):
            return _write_local(url, data)
        else:
            return _write_remote(url, data)

    def set_object_from_file(self, key, filename):
        """Set the value of 'key' in 'bucket' to equal the contents
           of the file located by 'filename'"""
        with open(filename, "rb") as FILE:
            data = FILE.read()
            self.set_object(key, data)

    def set_string_object(self, key, string_data):
        """Set the value of 'key' in 'bucket' to the string 'string_data'"""
        self.set_object(key, string_data.encode("utf-8"))

    def set_object_from_json(self, key, data):
        """Set the value of 'key' in 'bucket' to equal to contents
           of 'data', which has been encoded to json"""
        self.set_string_object(key, _json.dumps(data))


class ObjectReader:
    """This class provides functions for reading an object via a PAR"""
    def __init__(self, par=None):
        if par:
            if not isinstance(par, PAR):
                raise TypeError(
                    "You can only create an ObjectReader from a PAR")
            elif par.is_bucket():
                raise ValueError(
                    "You can only create an ObjectReader from a PAR that "
                    "represents an object: %s" % par)
            elif not par.is_readable():
                from Acquire.ObjectStore import PARPermissionsError
                raise PARPermissionsError(
                    "You cannot create an ObjectReader from a PAR without "
                    "read permissions: %s" % par)

            self._par = par
        else:
            self._par = None

    def get_object(self):
        """Return the binary data contained in this object"""
        if self._par is None:
            from Acquire.ObjectStore import PARError
            raise PARError("You cannot read data from an empty PAR")

        url = self._par.url()

        if url.startswith("file://"):
            return _read_local(url)
        else:
            return _read_remote(url)

    def get_object_as_file(self, filename):
        """Get the object contained in this PAR and write this to
           the file called 'filename'"""
        objdata = self.get_object()

        with open(filename, "wb") as FILE:
            FILE.write(objdata)

    def get_string_object(self):
        """Return the object behind this PAR as a string (raises exception
           if it is not a string)'"""
        data = self.get_object()

        try:
            return data.decode("utf-8")
        except Exception as e:
            raise TypeError(
                "The object behind this PAR cannot be converted to a string. "
                "Error is: %s" % str(e))

    def get_object_from_json(self):
        """Return an object constructed from json stored at behind
           this PAR. This raises an exception if there is no data
           or the PAR has expired
        """
        data = self.get_string_object()
        return _json.loads(data)


class ObjectWriter(ObjectReader):
    """This is an extension of ObjectReader that also allows writing to
       the object via the PAR
    """
    def __init__(self, par=None):
        if par:
            if not isinstance(par, PAR):
                raise TypeError(
                    "You can only create an ObjectReader from a PAR")
            elif par.is_bucket():
                raise ValueError(
                    "You can only create an ObjectReader from a PAR that "
                    "represents an object: %s" % par)
            elif not par.is_writeable():
                from Acquire.ObjectStore import PARPermissionsError
                raise PARPermissionsError(
                    "You cannot create an ObjectWriter from a PAR without "
                    "write permissions: %s" % par)

            self._par = par
        else:
            self._par = None

    def set_object(self, data):
        """Set the value of the object behind this PAR to the binary 'data'"""
        if self._par is None:
            from Acquire.ObjectStore import PARError
            raise PARError("You cannot write data to an empty PAR")

        url = self._par.url()

        if url.startswith("file://"):
            return _write_local(url, data)
        else:
            return _write_remote(url, data)

    def set_object_from_file(self, filename):
        """Set the value of the object behind this PAR to equal the contents
           of the file located by 'filename'"""
        with open(filename, "rb") as FILE:
            data = FILE.read()
            self.set_object(data)

    def set_string_object(self, string_data):
        """Set the value of the object behind this PAR to the
           string 'string_data'
        """
        self.set_object(string_data.encode("utf-8"))

    def set_object_from_json(self, data):
        """Set the value of the object behind this PAR to equal to contents
           of 'data', which has been encoded to json"""
        self.set_string_object(_json.dumps(data))
