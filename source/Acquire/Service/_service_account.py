
import os as _os
import json as _json

from cachetools import cached as _cached
from cachetools import LRUCache as _LRUCache

from Acquire.ObjectStore import ObjectStore as _ObjectStore
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes
from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import Mutex as _Mutex

from ._service import Service as _Service
from ._login_to_objstore import get_service_account_bucket \
                            as _get_service_account_bucket

from ._errors import ServiceError, ServiceAccountError, \
                     MissingServiceAccountError

# The cache can hold a maximum of 10 objects, and will replace the least
# recently used items first
_cache1 = _LRUCache(maxsize=10)  # used for service_info
_cache2 = _LRUCache(maxsize=10)  # used for admin_user


__all__ = ["setup_service_account",
           "get_service_info", "get_admin_user",
           "get_service_private_key",
           "get_service_private_certificate", "get_service_public_key",
           "get_service_public_certificate"]


# The key in the object store for the service object
_service_key = "_service_key"


# Cache this function as the data will rarely change, and this
# will prevent too many runs to the ObjectStore
@_cached(_cache1)
def _get_service_info_data():
    """Internal function that loads up the service info data from
       the object store.
    """

    # get the bucket again - can't pass as an argument as this is a cached
    # function - luckily _get_service_account_bucket is also a cached function
    try:
        bucket = _get_service_account_bucket()
    except ServiceAccountError as e:
        raise e
    except Exception as e:
        raise ServiceAccountError(
            "Cannot log into the service account: %s" % str(e))

    # find the service info from the object store
    try:
        service = _ObjectStore.get_object_from_json(bucket, _service_key)
    except Exception as e:
        raise MissingServiceAccountError(
            "Unable to load the service account for this service. An "
            "error occured while loading the data from the object "
            "store: %s" % str(e))

    if not service:
        raise MissingServiceAccountError(
            "You haven't yet created the service account "
            "for this service. Please create an account first.")

    return service


def _get_service_password():
    """Function used to get the primary password that locks the
       skeleton key that secures the entire tree of trust from the
       Service object
    """
    service_password = _os.getenv("SERVICE_PASSWORD")

    if service_password is None:
        raise ServiceAccountError(
            "You must supply a $SERVICE_PASSWORD")

    return service_password


def setup_service_account(canonical_url, service_type, username, password):
    """Call this function exactly once on a service to setup a new
       service that will servce at 'canonical_url', will be of
       the specified service_type. This will also create an administrating
       user called 'username', which will be secured with the
       passed password. This will return the provisioning_uri that will
       allow remote login to the service admin user account
    """
    bucket = _get_service_account_bucket()

    from Acquire.ObjectStore import Mutex as _Mutex

    # ensure that this is the only time the service is set up
    mutex = _Mutex(key=_service_key, bucket=bucket)
    service_info = _ObjectStore.get_string_object(bucket, _service_key)

    if service_info is not None:
        raise ServiceAccountError(
            "You cannot setup the service account twice. If you need to "
            "set the service up again, then manually log into the "
            "object store and delete the data associated with the key "
            "%s" % _service_key)

    service = _Service(service_url=canonical_url, service_type=service_type)

    # write the service data, encrypted using the service password
    service_password = _get_service_password()
    service_data = service.to_data(service_password)

    # now create the new user account that will be used to administer
    # the service
    from Acquire.Identity import UserAccount as _UserAccount
    from Acquire.Crypto import PrivateKey as _PrivateKey

    admin_user = _UserAccount(username=username)
    admin_password = _PrivateKey.random_passphrase()
    otp = admin_user.reset_password(admin_password)
    admin_secret = otp._secret

    admin_data = {"account": admin_user.to_data(),
                  "password": admin_password,
                  "otpsecret": admin_secret}

    admin_secret = service.skeleton_key().encrypt(_json.dumps(admin_data))

    # everything is done, so now write this data to the object store
    _ObjectStore.set_object_from_json(bucket, _service_key, service_data)
    _ObjectStore.set_string_object(bucket, "%s/admin_user" % _service_key,
                                   _bytes_to_string(admin_secret))

    # we can (finally!) release the mutex, as everyone else should now
    # be able to see the account
    mutex.unlock()

    # clear the caches to ensure they grab the new service and account info
    _cache1.clear()
    _cache2.clear()

    return otp.provisioning_uri(username="%s@%s" % (admin_user.username(),
                                                    canonical_url),
                                issuer="Acquire")


@_cached(_cache2)
def _get_admin_user_data():
    """Internal function that loads up the data for the admin
       user from the object store
    """
    # get the bucket again - can't pass as an argument as this is a cached
    # function - luckily _get_service_account_bucket is also a cached function
    try:
        bucket = _get_service_account_bucket()
    except ServiceAccountError as e:
        raise e
    except Exception as e:
        raise ServiceAccountError(
            "Cannot log into the service account: %s" % str(e))

    # find the service info from the object store
    try:
        key = "%s/admin_user" % _service_key
        admin_data = _ObjectStore.get_string_object(bucket, key)
    except Exception as e:
        raise MissingServiceAccountError(
            "Unable to load the Admin User for this service. An "
            "error occured while loading the data from the object "
            "store: %s" % str(e))

    if not admin_data:
        raise MissingServiceAccountError(
            "You haven't yet created the Admin User for the service account "
            "for this service. Please create an Admin User first.")

    return admin_data


@_cached(_cache1)
def get_service_info(need_private_access=False):
    """Return the service info object for this service. If private
       access is needed then this will decrypt and access the private
       keys and signing certificates, which is slow if you just need
       the public certificates.
    """
    try:
        service = _get_service_info_data()
    except Exception as e:
        raise MissingServiceAccountError(
            "Unable to read the service info from the object store! : %s" %
            str(e))

    service_password = None

    if need_private_access:
        service_password = _get_service_password()

    try:
        if service_password:
            service = _Service.from_data(service, service_password)
        else:
            service = _Service.from_data(service)

    except Exception as e:
        raise MissingServiceAccountError(
            "Unable to create the ServiceAccount object: %s" % str(e))

    return service


@_cached(_cache2)
def get_admin_user():
    """Function called to return the admin user account for this service.
       This account will already be logged into a valid LoginSession. This
       returns the user account as a Acquire.Client.User object, which can
       be used to sign authorisations or perform other tasks just like
       any normal account
    """
    try:
        admin_user_data = _get_admin_user_data()
    except Exception as e:
        raise MissingServiceAccountError(
            "Unable to read the Admin User from the object store! : %s" %
            str(e))

    # we need to decrypt using the skeleton key and then json-parse this data
    service = get_service_info(need_private_access=True)

    admin_user_data = service.skeleton_key().decrypt(
                            _string_to_bytes(admin_user_data))

    admin_user_data = _json.loads(admin_user_data)

    from Acquire.Identity import UserAccount as _UserAccount
    admin_user = _UserAccount.from_data(admin_user_data["account"])
    return admin_user.direct_login(admin_user_data["password"],
                                   admin_user_data["otpsecret"])


def _refresh_service_keys_and_certs(service):
    """This function will check if any key rotation is needed, and
       if so, it will automatically refresh the keys and certificates.
       The old keys and certificates will be stored in a database of
       old keys and certificates
    """
    if not service.should_refresh_keys():
        return service

    # save the old keys
    oldkeys = service.dump_keys()

    # generate new keys
    last_update = service.last_key_update()
    service.refresh_keys()

    # now lock the object store so that we are the only function
    # that can write the new keys to global state
    bucket = _get_service_account_bucket()
    m = _Mutex(key=service.uid(), bucket=bucket)

    service_data = _ObjectStore.get_object_from_json(bucket, _service_key)
    service_info = _Service.from_data(service_data)

    if service_info.last_key_update() == last_update:
        # no-one else has beaten us - write the updated keys to global state
        _ObjectStore.set_object_from_json(bucket, _service_key,
                                          service.to_data(
                                              _get_service_password()))
        m.unlock()

        # now write the old keys to storage
        key = "%s/oldkeys/%s" % (_service_key, oldkeys["datetime"])
        _ObjectStore.set_object_from_json(bucket, key, oldkeys)
    else:
        m.unlock()

    # clear the cache as we will need to load a new object
    _cache1.clear()

    return get_service_info(need_private_access=True)


def get_service_private_key(fingerprint=None):
    """This function returns the private key for this service"""
    s = get_service_info(need_private_access=True)
    s = _refresh_service_keys_and_certs(s)
    key = s.private_key()

    if fingerprint:
        if key.fingerprint() != fingerprint:
            key = s.last_key()

        if key.fingerprint() != fingerprint:
            raise ServiceAccountError(
                "Cannot find a private key for '%s' that matches "
                "the fingerprint %s" % (str(s), fingerprint))

    return key


def get_service_private_certificate(fingerprint=None):
    """This function returns the private signing certificate
       for this service
    """
    s = get_service_info(need_private_access=True)
    s = _refresh_service_keys_and_certs(s)
    cert = s.private_certificate()

    if fingerprint:
        if cert.fingerprint() != fingerprint:
            raise ServiceAccountError(
                "Cannot find a private certificate for '%s' that matches "
                "the fingerprint %s" % (str(s), fingerprint))

    return cert


def get_service_public_key(fingerprint=None):
    """This function returns the public key for this service"""
    s = get_service_info(need_private_access=False)
    key = s.public_key()

    if fingerprint:
        if key.fingerprint() != fingerprint:
            raise ServiceAccountError(
                "Cannot find a public key for '%s' that matches "
                "the fingerprint %s" % (str(s), fingerprint))

    return key


def get_service_public_certificate(fingerprint=None):
    """This function returns the public certificate for this service"""
    s = get_service_info(need_private_access=False)
    cert = s.public_certificate()

    if fingerprint:
        if cert.fingerprint() != fingerprint:
            cert = s.last_certificate()

        if cert.fingerprint() != fingerprint:
            raise ServiceAccountError(
                "Cannot find a public certificate for '%s' that matches "
                "the fingerprint %s" % (str(s), fingerprint))

    return cert
