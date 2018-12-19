
import os as _os
import json as _json

from cachetools import cached as _cached
from cachetools import LRUCache as _LRUCache

from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._service import Service as _Service
from ._login_to_objstore import login_to_service_account \
                            as _login_to_service_account

from ._errors import ServiceError, ServiceAccountError, \
                     MissingServiceAccountError

# The cache can hold a maximum of 10 objects, and will replace the least
# recently used items first
_cache1 = _LRUCache(maxsize=10)
_cache2 = _LRUCache(maxsize=10)


__all__ = ["get_service_info", "get_service_private_key",
           "get_service_private_certificate", "get_service_public_key",
           "get_service_public_certificate"]


# Cache this function as the data will rarely change, and this
# will prevent too many runs to the ObjectStore
@_cached(_cache1)
def _get_service_info_data():
    """Internal function that loads up the service info data from
       the object store.
    """

    # get the bucket again - can't pass as an argument as this is a cached
    # function - luckily _login_to_service_account is also a cached function
    bucket = _login_to_service_account()

    # find the service info from the object store
    service_key = "_service_info"

    try:
        service = _ObjectStore.get_object_from_json(bucket, service_key)
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


@_cached(_cache2)
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
        service_password = _os.getenv("SERVICE_PASSWORD")

        if service_password is None:
            raise ServiceAccountError(
                "You must supply a $SERVICE_PASSWORD")

    try:
        if service_password:
            service = _Service.from_data(service, service_password)
        else:
            service = _Service.from_data(service)

    except Exception as e:
        raise MissingServiceAccountError(
            "Unable to create the ServiceAccount object: %s" % str(e))

    return service


def get_service_private_key():
    """This function returns the private key for this service"""
    return get_service_info(need_private_access=True).private_key()


def get_service_private_certificate():
    """This function returns the private signing certificate
       for this service
    """
    return get_service_info(need_private_access=True).private_certificate()


def get_service_public_key():
    """This function returns the public key for this service"""
    return get_service_info(need_private_access=False).public_key()


def get_service_public_certificate():
    """This function returns the public certificate for this service"""
    return get_service_info(need_private_access=False).public_certificate()
