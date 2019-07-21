
import io as _io
import datetime as _datetime
import uuid as _uuid
import json as _json
import os as _os
import copy as _copy

__all__ = ["GCP_ObjectStore"]


def _sanitise_bucket_name(bucket_name, unique_prefix):
    """This function sanitises the passed bucket name. It will always
        return a valid bucket name. If "None" is passed, then a new,
        unique bucket name will be generated

        This will always prepend 'unique_prefix' to the bucket name,
        as google requires globally unique names...
    """

    if bucket_name is None:
        bucket_name = str(_uuid.uuid4())

    unique_prefix = ("_".join(unique_prefix.split())).lower()
    bucket_name = ("_".join(bucket_name.split())).lower()

    bucket_name = "%s__%s" % (unique_prefix, bucket_name)

    if len(bucket_name) > 63:
        bucket_name = bucket_name[0:63]

    bucket_name = bucket_name.replace("google", "acquir")

    return bucket_name


def _clean_key(key):
    """This function cleans and returns a key so that it is suitable
       for use both as a key and a directory/file path
       e.g. it removes double-slashes

       Args:
            key (str): Key to clean
       Returns:
            str: Cleaned key

    """
    key = _os.path.normpath(key)

    if len(key) > 1024:
        from Acquire.ObjectStore import ObjectStoreError
        raise ObjectStoreError(
            "The object store does not support keys with longer than "
            "1024 characters (%s) - %s" % (len(key), key))

        # if this becomes a problem then we will implement a 'tinyurl'
        # to shorten keys and use this function to lookup long keys

    return key

def _get_driver_details_from_par(par):
    """Internal function used to get the GCP driver details from the
       passed OSPar (pre-authenticated request)

       Args:
            par (OSPar): PAR holding details
        Args:
            dict: Dictionary holding GCP driver details
    """
    from Acquire.ObjectStore import datetime_to_string \
        as _datetime_to_string

    import copy as _copy
    details = _copy.copy(par._driver_details)

    if details is None:
        return {}
    else:
        # fix any non-string/number objects
        details["created_datetime"] = _datetime_to_string(
                                        details["created_datetime"])

    return details

def _get_driver_details_from_data(data):
    """Internal function used to get the GCP driver details from the
       passed data

       Args:
            data (dict): Dict holding GCP driver details
       Returns:
            dict: Dict holding GCP driver details
    """
    from Acquire.ObjectStore import string_to_datetime \
        as _string_to_datetime

    import copy as _copy
    details = _copy.copy(data)

    if "created_datetime" in details:
        details["created_datetime"] = _string_to_datetime(
                                            details["created_datetime"])

    return details


class GCP_ObjectStore:
    """This is the backend that abstracts using the Google Cloud Platform
       object store
    """

    @staticmethod
    def create_bucket(bucket, bucket_name):
        """Create and return a new bucket in the object store called
           'bucket_name'. This will raise an
           ObjectStoreError if this bucket already exists
        """
        new_bucket = _copy.copy(bucket)

        try:
            from google.cloud import storage as _storage
            client = new_bucket["client"]
            bucket_name = _sanitise_bucket_name(bucket_name,
                                                bucket["unique_suffix"])
            bucket_obj = _storage.Bucket(client, name=bucket_name)
            bucket_obj.location = bucket["bucket"].location
            bucket_obj.storage_class = "REGIONAL"
            new_bucket["bucket"] = client.create_bucket(bucket_obj)
            new_bucket["bucket_name"] = str(bucket_name)
        except Exception as e:
            # couldn't create the bucket - likely because it already
            # exists - try to connect to the existing bucket
            from Acquire.ObjectStore import ObjectStoreError
            raise ObjectStoreError(
                "Unable to create the bucket '%s', likely because it "
                "already exists: %s" % (bucket_name, str(e)))

        return new_bucket

    @staticmethod
    def get_bucket(bucket, bucket_name, create_if_needed=True):
        """Find and return a new bucket in the object store called
           'bucket_name'. If 'create_if_needed' is True
           then the bucket will be created if it doesn't exist. Otherwise,
           if the bucket does not exist then an exception will be raised.
        """
        new_bucket = _copy.copy(bucket)

        # try to get the existing bucket
        client = new_bucket["client"]
        sanitised_name = _sanitise_bucket_name(bucket_name,
                                               bucket["unique_suffix"])
        new_bucket["bucket_name"] = sanitised_name
        try:
            existing_bucket = client.get_bucket(sanitised_name)
        except:
            existing_bucket = None

        if existing_bucket:
            new_bucket["bucket"] = existing_bucket
            return new_bucket

        if create_if_needed:
            try:
                new_bucket = GCP_ObjectStore.create_bucket(bucket, bucket_name)
                existing_bucket = new_bucket["bucket"]
            except:
                existing_bucket = None

        if existing_bucket is None:
            from Acquire.ObjectStore import ObjectStoreError
            raise ObjectStoreError(
                "There is not bucket called '%s'. Please check the "
                "access permissions." % bucket_name)

        new_bucket["bucket"] = existing_bucket

        return new_bucket

    @staticmethod
    def get_bucket_name(bucket):
        """Return the name of the passed bucket

           Args:
                bucket (dict): Bucket holding data
           Returns:
                str: Name of bucket
        """
        return bucket["bucket_name"]

    @staticmethod
    def is_bucket_empty(bucket):
        """Return whether or not the passed bucket is empty

           Args:
                bucket (dict): Bucket holding data
           Returns:
                bool: True if bucket empty, else False

        """
        it = bucket["bucket"].list_blobs(max_results=1)

        num_objs = 0
        for _obj in it:
            num_objs = num_objs + 1

        if num_objs == 0:
            return True
        else:
            return False

    @staticmethod
    def delete_bucket(bucket, force=False):
        """Delete the passed bucket. This should be used with caution.
           Normally you can only delete a bucket if it is empty. If
           'force' is True then it will remove all objects/pars from
           the bucket first, and then delete the bucket. This
           can cause a LOSS OF DATA!

           Args:
                bucket (dict): Bucket to delete
                force (bool, default=False): If True, delete even
                if bucket is not empty. If False and bucket not empty
                raise PermissionError
           Returns:
                None
        """
        is_empty = GCP_ObjectStore.is_bucket_empty(bucket=bucket)

        if not is_empty:
            if force:
                GCP_ObjectStore.delete_all_objects(bucket=bucket)
            else:
                raise PermissionError(
                    "You cannot delete the bucket %s as it is not empty" %
                    GCP_ObjectStore.get_bucket_name(bucket=bucket))

        # the bucket is empty - delete it
        try:
            bucket['bucket'].delete()
        except Exception as e:
            from Acquire.ObjectStore import ObjectStoreError
            raise ObjectStoreError(
                "Unable to delete bucket '%s'. Please check the "
                "access permissions: Error %s" %
                (bucket['bucket_name'], str(e)))


    @staticmethod
    def create_par(bucket, encrypt_key, key=None, readable=True,
                   writeable=False, duration=3600, cleanup_function=None):
        """Create a pre-authenticated request for the passed bucket and
           key (if key is None then the request is for the entire bucket).
           This will return a OSPar object that will contain a URL that can
           be used to access the object/bucket. If writeable is true, then
           the URL will also allow the object/bucket to be written to.
           PARs are time-limited. Set the lifetime in seconds by passing
           in 'duration' (by default this is one hour)

           Args:
                bucket (dict): Bucket to create OSPar for
                encrypt_key (PublicKey): Public key to
                encrypt PAR
                key (str, default=None): Key
                readable (bool, default=True): If bucket is readable
                writeable (bool, default=False): If bucket is writeable
                duration (int, default=3600): Duration OSPar should be
                valid for in seconds
                cleanup_function (function, default=None): Cleanup
                function to be passed to PARRegistry

           Returns:
                OSPar: Pre-authenticated request for the bucket
        """
        from Acquire.Crypto import PublicKey as _PublicKey

        if not isinstance(encrypt_key, _PublicKey):
            from Acquire.Client import PARError
            raise PARError(
                "You must supply a valid PublicKey to encrypt the "
                "returned OSPar")

        is_bucket = (key is None)

        if writeable:
            method = "PUT"
        elif readable:
            method = "GET"
        else:
            from Acquire.ObjectStore import ObjectStoreError
            raise ObjectStoreError(
                "Unsupported permissions model for OSPar!")

        try:
            # get the UTC datetime when this OSPar should expire
            from Acquire.ObjectStore import get_datetime_now as _get_datetime_now
            created_datetime = _get_datetime_now()
            expires_datetime = _get_datetime_now() + _datetime.timedelta(seconds=duration)
            bucket_obj = bucket["bucket"]
            if is_bucket:
                url = bucket_obj.generate_signed_url(version='v4', expiration=expires_datetime, method=method)
            else:
                blob = bucket_obj.blob(key)
                url = blob.generate_signed_url(version='v4', expiration=expires_datetime, method=method)

        except Exception as e:
            # couldn't create the preauthenticated request
            from Acquire.ObjectStore import ObjectStoreError
            raise ObjectStoreError(
                "Unable to create the OSPar '%s': %s" %
                (key, str(e)))

        if url is None:
            from Acquire.ObjectStore import ObjectStoreError
            raise ObjectStoreError(
                "Unable to create the signed URL!")

        # get the checksum for this URL - used to validate the close
        # request
        from Acquire.ObjectStore import OSPar as _OSPar
        from Acquire.ObjectStore import OSParRegistry as _OSParRegistry
        url_checksum = _OSPar.checksum(url)
        bucket_name = bucket["bucket_name"]
        driver_details = {"driver": "gcp",
                          "bucket": bucket_name,
                          "created_datetime": created_datetime}

        par = _OSPar(url=url, encrypt_key=encrypt_key,
                     key=key,
                     expires_datetime=expires_datetime,
                     is_readable=readable,
                     is_writeable=writeable,
                     driver_details=driver_details)

        _OSParRegistry.register(par=par,
                                url_checksum=url_checksum,
                                details_function=_get_driver_details_from_par,
                                cleanup_function=cleanup_function)

        return par

    @staticmethod
    def close_par(par=None, par_uid=None, url_checksum=None):
        """Close the passed OSPar, which provides access to data in the
           passed bucket

           Args:
                par (OSPar, default=None): OSPar to close bucket
                par_uid (str, default=None): UID for OSPar
                url_checksum (str, default=None): Checksum to
                pass to PARRegistry
           Returns:
                None
        """
        from Acquire.ObjectStore import OSParRegistry as _OSParRegistry

        if par is None:
            par = _OSParRegistry.get(
                            par_uid=par_uid,
                            details_function=_get_driver_details_from_data,
                            url_checksum=url_checksum)

        from Acquire.ObjectStore import OSPar as _OSPar
        if not isinstance(par, _OSPar):
            raise TypeError("The OSPar must be of type OSPar")

        if par.driver() != "gcp":
            raise ValueError("Cannot delete a OSPar that was not created "
                             "by the GCP object store")

        # close the OSPar - this will trigger any close_function(s)
        _OSParRegistry.close(par=par)

    @staticmethod
    def get_object(bucket, key):
        """Return the binary data contained in the key 'key' in the
           passed bucket

           Args:
                bucket (dict): Bucket containing data
                key (str): Key for data in bucket
           Returns:
                bytes: Binary data

        """

        key = _clean_key(key)

        blob = bucket["bucket"].blob(key)

        try:
            response = blob.download_as_string()
            is_chunked = False
        except:
            try:
                blob = bucket["bucket"].blob("%s/1" % key)
                response = blob.download_as_string()
                is_chunked = True
            except:
                is_chunked = False
                pass

            # Raise the original error
            if not is_chunked:
                from Acquire.ObjectStore import ObjectStoreError
                raise ObjectStoreError("No data at key '%s'" % key)

        data = response

        if is_chunked:
            # keep going through to find more chunks
            next_chunk = 1

            while True:
                next_chunk += 1

                try:
                    blob = bucket["bucket"].blob("%s/%s" % (key, next_chunk))
                    response = blob.download_as_string()
                except:
                    response = None
                    break

                if not data:
                    data = response
                else:
                    data += response

        return data

    @staticmethod
    def take_object(bucket, key):
        """Take (delete) the object from the object store, returning
           the object

           Args:
                bucket (dict): Bucket containing data
                key (str): Key for data

           Returns:
                bytes: Binary data
        """
        # ideally the get and delete should be atomic... would like this API
        data = GCP_ObjectStore.get_object(bucket, key)

        try:
            GCP_ObjectStore.delete_object(bucket, key)
        except:
            pass

        return data

    @staticmethod
    def get_all_object_names(bucket, prefix=None, without_prefix=False):
        """Returns the names of all objects in the passed bucket

           Args:
                bucket (dict): Bucket containing data
                prefix (str): Prefix for data
                without_prefix (str): Whether or not to include the prefix
                                      in the object name
           Returns:
                list: List of all objects in bucket

        """
        if prefix is not None:
            prefix = _clean_key(prefix)

        blobs = bucket["bucket"].list_blobs(prefix=prefix)

        names = []

        if without_prefix:
            prefix_len = len(prefix)

        for obj in blobs:
            if prefix:
                if obj.name.startswith(prefix):
                    name = obj.name
            else:
                name = obj.name

            while name.endswith("/"):
                name = name[0:-1]

            while name.startswith("/"):
                name = name[1:]

            if without_prefix:
                name = name[prefix_len:]

                while name.startswith("/"):
                    name = name[1:]

            if len(name) > 0:
                names.append(name)

        return names

    @staticmethod
    def set_object(bucket, key, data):
        """Set the value of 'key' in 'bucket' to binary 'data'

           Args:
                bucket (dict): Bucket containing data
                key (str): Key for data in bucket
                data (bytes): Binary data to store in bucket

           Returns:
                None
        """
        if data is None:
            data = b'0'

        if isinstance(data, str):
            data = data.encode("utf-8")

        key = _clean_key(key)

        blob = bucket["bucket"].blob(key)
        blob.upload_from_string(data)

    @staticmethod
    def delete_all_objects(bucket, prefix=None):
        """Deletes all objects...

           Args:
                bucket (dict): Bucket containing data
                prefix (str, default=None): Prefix for data,
                currently unused
            Returns:
                None
        """
        blobs = bucket["bucket"].list_blobs()

        for blob in blobs:
            blob.delete()

    @staticmethod
    def delete_object(bucket, key):
        """Removes the object at 'key'

           Args:
                bucket (dict): Bucket containing data
                key (str): Key for data
           Returns:
                None
        """
        try:
            bucket["bucket"].blob(key).delete()

        except:
            pass

    @staticmethod
    def get_size_and_checksum(bucket, key):
        """Return the object size (in bytes) and MD5 checksum of the
           object in the passed bucket at the specified key

           Args:
                bucket (dict): Bucket containing data
                key (str): Key for object
           Returns:
                tuple (int, str): Size and MD5 checksum of object

        """
        key = _clean_key(key)

        try:
            blob = bucket["bucket"].get_blob(key)
            checksum = blob.md5_hash
            content_length = blob.size
        except:
            from Acquire.ObjectStore import ObjectStoreError
            raise ObjectStoreError("No data at key '%s'" % key)
        # the checksum is a base64 encoded Content-MD5 header
        # described as standard part of HTTP RFC 2616. Need to
        # convert this back to a hexdigest
        import binascii as _binascii
        import base64 as _base64
        md5sum = _binascii.hexlify(_base64.b64decode(checksum)).decode("utf-8")

        return (int(content_length), md5sum)
