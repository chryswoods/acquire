
import os as _os
import json as _json

from cachetools import cached as _cached
from cachetools import TTLCache as _TTLCache

from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._service import Service as _Service
from ._login_to_objstore import login_to_service_account \
                            as _login_to_service_account

from ._errors import ServiceError, ServiceAccountError, \
                     MissingServiceAccountError

# The cache can hold a maximum of 50 objects, and will be renewed
# every 300 seconds (so any changes in this service's key would
# cause problems for a maximum of 300 seconds)
_cache = _TTLCache(maxsize=50, ttl=300)


__all__ = ["get_service_info", "get_service_private_key",
           "get_service_private_certificate", "get_service_public_key",
           "get_service_public_certificate"]


# Cache this function as the data will rarely change, and this
# will prevent too many runs to the ObjectStore
@_cached(_cache)
def _get_service_info_data():
    """Internal function that loads up the service info data from
       the object store.
    """
    bucket = _login_to_service_account()

    # find the service info from the object store
    service_key = "_service_info"

    service = _ObjectStore.get_object_from_json(bucket, service_key)

    if not service:
        raise MissingServiceAccountError(
            "You haven't yet created the service account "
            "for this service. Please create an account first.")

    return service


def get_service_info(need_private_access=False):
    """Return the service info object for this service. If private
       access is needed then this will decrypt and access the private
       keys and signing certificates, which is slow if you just need
       the public certificates.
    """
    service = _get_service_info_data()

    if need_private_access:
        service_password = _os.getenv("SERVICE_PASSWORD")

        if service_password is None:
            raise ServiceAccountError("You must supply a $SERVICE_PASSWORD")

        service = _Service.from_data(service, service_password)
    else:
        service = _Service.from_data(service)

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
