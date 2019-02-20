
import base64 as _base64

from cachetools import cached as _cached
from cachetools import LRUCache as _LRUCache

_cache_local_serviceinfo = _LRUCache(maxsize=5)
_cache_remote_serviceinfo = _LRUCache(maxsize=20)

__all__ = ["get_trusted_service",
           "get_remote_service", "get_checked_remote_service",
           "clear_services_cache"]


def clear_services_cache():
    """Clear the caches of loaded services"""
    _cache_local_serviceinfo.clear()
    _cache_remote_serviceinfo.clear()


# Cached as the remove service information will not change too often
@_cached(_cache_local_serviceinfo)
def get_trusted_service(service_url=None, service_uid=None):
    """Return the trusted service info for the service with specified
       service_url or service_uid"""
    from Acquire.Service import is_running_service as _is_running_service

    if _is_running_service():
        from Acquire.Service import get_this_service as _get_this_service
        from Acquire.Service import Service as _Service
        from Acquire.Service import get_service_account_bucket as \
            _get_service_account_bucket
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.ObjectStore import url_to_encoded as \
            _url_to_encoded

        service = _get_this_service()

        if service.canonical_url() == service_url:
            # we trust ourselves :-)
            return service

        bucket = _get_service_account_bucket()

        uidkey = None

        if service_uid is not None:
            uidkey = "_trusted/uid/%s" % service_uid
            data = _ObjectStore.get_object_from_json(bucket, uidkey)
        elif service_url is not None:
            urlkey = "_trusted/url/%s" % _url_to_encoded(service_url)
            uidkey = _ObjectStore.get_string_object(bucket, urlkey)
            if uidkey is not None:
                data = _ObjectStore.get_object_from_json(bucket, uidkey)
        else:
            data = None

        if data is None:
            from Acquire.Service import ServiceAccountError
            if service_uid is not None:
                raise ServiceAccountError(
                    "We do not trust the service with UID '%s'" %
                    service_uid)
            else:
                raise ServiceAccountError(
                    "We do not trust the service at URL '%s'" %
                    service_url)

        remote_service = _Service.from_data(data)

        if remote_service.should_refresh_keys():
            # need to update the keys in our copy of the service
            remote_service.refresh_keys()

            if uidkey is not None:
                _ObjectStore.set_object_from_json(bucket, uidkey,
                                                  remote_service.to_data())

        return remote_service
    else:
        # this is running on the client
        from Acquire.Client import Service as _Service
        return _Service(service_url=service_url, service_uid=service_uid)


# Cached to stop us sending too many requests for info to remote services
@_cached(_cache_remote_serviceinfo)
def get_remote_service(service_url):
    """This function returns the service info for the service at
       'service_url'
    """
    from Acquire.Crypto import get_private_key as _get_private_key
    from Acquire.Service import call_function as _call_function
    from Acquire.Service import Service as _Service

    key = _get_private_key("function")

    try:
        response = _call_function(service_url, response_key=key)
    except Exception as e:
        from Acquire.Service import ServiceError
        raise ServiceError("Cannot get information about '%s': %s" %
                           (service_url, str(e)))

    from Acquire.Crypto import SignatureVerificationError \
        as _SignatureVerificationError

    try:
        return _Service.from_data(response["service_info"],
                                  verify_data=True)
    except _SignatureVerificationError:
        raise
    except Exception as e:
        from Acquire.Service import ServiceError
        raise ServiceError(
                "Cannot extract service info for '%s' from '%s': %s" %
                (service_url, str(response), str(e)))


def get_checked_remote_service(service_url, public_cert):
    """This function returns the service info for the service at
       'service_url'. This checks that the info has been signed
       correctly by the passed public certificate
    """
    from Acquire.Crypto import get_private_key as _get_private_key
    from Acquire.Service import call_function as _call_function
    from Acquire.Service import Service as _Service

    key = _get_private_key("function")

    try:
        response = _call_function(service_url, response_key=key,
                                  public_cert=public_cert)
    except Exception as e:
        from Acquire.Service import ServiceError
        raise ServiceError("Cannot get information about '%s': %s" %
                           (service_url, str(e)))

    from Acquire.Crypto import SignatureVerificationError \
        as _SignatureVerificationError

    try:
        return _Service.from_data(response["service_info"],
                                  verify_data=True)
    except _SignatureVerificationError:
        raise
    except Exception as e:
        from Acquire.Service import ServiceError
        raise ServiceError(
                "Cannot extract service info for '%s' from '%s': %s" &
                (service_url, str(response), str(e)))
