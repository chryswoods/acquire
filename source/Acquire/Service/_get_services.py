
import base64 as _base64

from cachetools import cached as _cached
from cachetools import LRUCache as _LRUCache

from Acquire.ObjectStore import ObjectStore as _ObjectStore
from Acquire.Crypto import PrivateKey as _PrivateKey

from ._service import Service as _Service
from ._function import call_function as _call_function

from ._login_to_objstore import login_to_service_account as \
                               _login_to_service_account

from ._errors import ServiceError, ServiceAccountError

# The cache can hold a maximum of 50 objects, and will replace the least
# recently used items first
_cache = _LRUCache(maxsize=50)

__all__ = ["url_to_encoded", "get_trusted_service_info",
           "set_trusted_service_info", "remove_trusted_service_info",
           "get_remote_service_info"]


def url_to_encoded(url):
    """Return an encoding of the passed url that is safe to use
       as a name, filename or key in an object store
    """
    return _base64.b64encode(url.encode("utf-8")).decode("utf-8")


def set_trusted_service_info(service_url, service):
    """Set the trusted service info for 'service_url' to 'service'"""
    bucket = _login_to_service_account()
    _ObjectStore.set_object_from_json(
                                bucket,
                                "services/%s" % url_to_encoded(service_url),
                                service.to_data())


def remove_trusted_service_info(service_url):
    """Remove the passed 'service_url' from the list of trusted services"""
    bucket = _login_to_service_account()
    try:
        _ObjectStore.delete_object(bucket,
                                   "services/%s" % url_to_encoded(service_url))
    except:
        pass


# Cached as the remove service information will not change too often
@_cached(_cache)
def get_trusted_service_info(service_url):
    """Return the trusted service info for 'service_url'"""
    bucket = _login_to_service_account()
    data = _ObjectStore.get_object_from_json(
                            bucket,
                            "services/%s" % url_to_encoded(service_url))

    if data is None:
        raise ServiceAccountError("We do not trust the service at '%s'" %
                                  service_url)

    return _Service.from_data(data)


# Cached to stop us sending too many requests for info to remote services
@_cached(_cache)
def get_remote_service_info(service_url):
    """This function returns the service info for the service at
       'service_url'
    """

    key = _PrivateKey()

    try:
        response = _call_function(service_url, response_key=key)
    except Exception as e:
        raise ServiceError("Cannot get information about '%s': %s" %
                           (service_url, str(e)))

    try:
        return _Service.from_data(response["service_info"])
    except Exception as e:
        raise ServiceError(
                "Cannot extract service info for '%s' from '%s': %s" &
                (service_url, str(response), str(e)))
