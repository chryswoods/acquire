
import base64 as _base64

from cachetools import cached as _cached
from cachetools import LRUCache as _LRUCache

from Acquire.ObjectStore import ObjectStore as _ObjectStore
from Acquire.Crypto import PrivateKey as _PrivateKey

from ._service import Service as _Service
from ._function import call_function as _call_function

from ._service_account import get_service_info as _get_service_info

from ._login_to_objstore import login_to_service_account as \
                               _login_to_service_account

from ._errors import ServiceError, ServiceAccountError

_cache_local_serviceinfo = _LRUCache(maxsize=5)
_cache_remote_serviceinfo = _LRUCache(maxsize=20)

__all__ = ["url_to_encoded", "trust_service", "untrust_service",
           "get_trusted_service_info",
           "get_remote_service_info", "get_checked_remote_service_info",
           "clear_services_cache"]


def clear_services_cache():
    """Clear the caches of loaded services"""
    _cache_local_serviceinfo.clear()
    _cache_remote_serviceinfo.clear()


def url_to_encoded(url):
    """Return an encoding of the passed url that is safe to use
       as a name, filename or key in an object store
    """
    return _base64.b64encode(url.encode("utf-8")).decode("utf-8")


def trust_service(service, authorisation):
    """Trust the passed service. This will record this service as trusted,
       e.g. saving the keys and certificates for this service and allowing
       it to be used for the specified type. You must pass in a valid
       admin_user authorisation for this service
    """
    local_service = _get_service_info(need_private_access=True)
    local_service.assert_admin_authorised(authorisation,
                                          "trust %s" % service.uid())

    bucket = _login_to_service_account()
    urlkey = "_trusted/url/%s" % url_to_encoded(service.canonical_url())
    uidkey = "_trusted/uid/%s" % service.uid()
    service_data = service.to_data()

    # store the trusted service by both canonical_url and uid
    _ObjectStore.set_object_from_json(bucket, uidkey, service_data)
    _ObjectStore.set_string_object(bucket, urlkey, uidkey)

    clear_services_cache()


def untrust_service(service, authorisation):
    """Stop trusting the passed service. This will remove the service
       as being trusted. You must pass in a valid admin_user authorisation
       for this service
    """
    local_service = _get_service_info(need_private_access=True)
    local_service.assert_admin_authorised(authorisation,
                                          "trust %s" % service.uid())

    bucket = _login_to_service_account()
    urlkey = "_trusted/url/%s" % url_to_encoded(service.canonical_url())
    uidkey = "_trusted/uid/%s" % service.uid()

    # delete the trusted service by both canonical_url and uid
    try:
        _ObjectStore.delete_object(bucket, uidkey)
    except:
        pass

    try:
        _ObjectStore.delete_object(bucket, urlkey)
    except:
        pass

    clear_services_cache()


# Cached as the remove service information will not change too often
@_cached(_cache_local_serviceinfo)
def get_trusted_service_info(service_url=None, service_uid=None):
    """Return the trusted service info for the service with specified
       service_url or service_uid"""
    service = _get_service_info()

    if service.canonical_url() == service_url:
        # we trust ourselves :-)
        return service

    bucket = _login_to_service_account()

    if service_uid is not None:
        uidkey = "_trusted/uid/%s" % service_uid
        data = _ObjectStore.get_object_from_json(bucket, uidkey)
    elif service_url is not None:
        urlkey = "_trusted/url/%s" % url_to_encoded(service_url)
        uidkey = _ObjectStore.get_string_object(bucket, urlkey)
        if uidkey is not None:
            data = _ObjectStore.get_object_from_json(bucket, uidkey)
    else:
        data = None

    if data is None:
        if service_uid is not None:
            raise ServiceAccountError(
                "We do not trust the service with UID '%s'" %
                service_uid)
        else:
            raise ServiceAccountError(
                "We do not trust the service at URL '%s'" %
                service_url)

    return _Service.from_data(data)


# Cached to stop us sending too many requests for info to remote services
@_cached(_cache_remote_serviceinfo)
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


def get_checked_remote_service_info(service_url, public_cert):
    """This function returns the service info for the service at
       'service_url'. This checks that the info has been signed
       correctly by the passed public certificate
    """
    key = _PrivateKey()

    try:
        response = _call_function(service_url, response_key=key,
                                  public_cert=public_cert)
    except Exception as e:
        raise ServiceError("Cannot get information about '%s': %s" %
                           (service_url, str(e)))

    try:
        return _Service.from_data(response["service_info"])
    except Exception as e:
        raise ServiceError(
                "Cannot extract service info for '%s' from '%s': %s" &
                (service_url, str(response), str(e)))
