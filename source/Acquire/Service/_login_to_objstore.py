
import os as _os
import json as _json

from cachetools import cached as _cached
from cachetools import TTLCache as _TTLCache

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

from ._errors import ServiceAccountError

# The cache can hold a maximum of 50 objects, and will be renewed
# every 300 seconds (so any changes in this service's key would
# cause problems for a maximum of 300 seconds)
_cache = _TTLCache(maxsize=50, ttl=300)

__all__ = ["login_to_service_account"]

_current_testing_objstore = None


# Cache this function as the result changes very infrequently, as involves
# lots of round trips to the object store, and it will give the same
# result regardless of which Fn function on the service makes the call
@_cached(_cache)
def login_to_service_account(testing_dir=None):
    """This function logs into the object store account of the service account.
       Accessing the object store means being able to access
       all resources and which can authorise the creation
       of access all resources on the object store. Obviously this is
       a powerful account, so only log into it if you need it!!!

       The login information should not be put into a public
       repository or stored in plain text. In this case,
       the login information is held in an environment variable
       (which should be encrypted or hidden in some way...)
    """

    # read the password for the secret key from the filesystem
    try:
        with open("secret_key", "r") as FILE:
            password = FILE.readline()[0:-1]
    except:
        password = None

        # we must be in testing mode...
        from Acquire.ObjectStore import use_testing_object_store_backend as \
            _use_testing_object_store_backend

        # see if this is running in testing mode...
        global _current_testing_objstore
        if testing_dir:
            _current_testing_objstore = testing_dir
            return _use_testing_object_store_backend(testing_dir)
        elif _current_testing_objstore:
            return _use_testing_object_store_backend(_current_testing_objstore)

    if password is None:
        raise ServiceAccountError(
            "You need to supply login credentials via the 'secret_key' "
            "file, and 'SECRET_KEY' and 'SECRET_CONFIG' environment "
            "variables! %s" % testing_dir)

    # use the password to decrypt the SECRET_KEY in the config
    secret_key = _PrivateKey.from_data(_json.loads(_os.getenv("SECRET_KEY")),
                                       password)

    # use the secret_key to decrypt the config in SECRET_CONFIG
    config = _json.loads(secret_key.decrypt(
                         _string_to_bytes(_os.getenv("SECRET_CONFIG")))
                         .decode("utf-8"))

    # get info from this config
    access_data = config["LOGIN"]
    bucket_data = config["BUCKET"]

    # save the service password to the environment
    _os.environ["SERVICE_PASSWORD"] = config["PASSWORD"]

    # we have OCI login details, so make sure that we are using
    # the OCI object store backend
    from Acquire.ObjectStore import use_oci_object_store_backend as \
        _use_oci_object_store_backend

    _use_oci_object_store_backend()

    # now login and create/load the bucket for this account
    try:
        from ._oci_account import OCIAccount as _OCIAccount

        account_bucket = _OCIAccount.create_and_connect_to_bucket(
                                    access_data,
                                    bucket_data["compartment"],
                                    bucket_data["bucket"])
    except Exception as e:
        raise ServiceAccountError(
             "Error connecting to the service account: %s" % str(e))

    return account_bucket
