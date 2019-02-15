
from Acquire.Service import get_remote_service_info as _get_remote_service_info
from Acquire.Service import ServiceError

from cachetools import LRUCache as _LRUCache
from cachetools import cached as _cached

__all__ = ["Service"]

_cache_service_lookup = _LRUCache(maxsize=5)


@_cached(_cache_service_lookup)
def _get_remote_service(service_url):
    """Call this function to get the Service info of a remote Service.
       This will check if we have seen the service before. If so, then
       we will ensure that this is the correct service. If not, then
       we will prompt the user to validate that this is the right
       service
    """
    from Acquire.Client import Wallet as _Wallet
    return _Wallet.get_service(service_url)


class Service:
    """This class provides a client-side wrapper to fetch or set-up
       a service
    """
    def __init__(self, service_url):
        """Construct the service that is accessed at the remote
           URL 'service_url'. This will fetch and return the
           details of the remote service. This wrapper is a
           chameleon class, and will transform into the
           class type of the fetched service, e.g.

            service = Acquire.Client.Service("https://identity_service_url")
            service.__class__ == Acquire.Identity.IdentityService
        """
        try:
            service = _get_remote_service(service_url)

            from copy import copy as _copy
            self.__dict__ = _copy(service.__dict__)
            self.__class__ = service.__class__
        except Exception as e:
            _cache_service_lookup.clear()
            self._failed = True
            raise e

    def call_function(self, function=None, args=None):
        """Call the function 'function' using the passed arguments
           'args' on this service
        """
        if self._failed:
            raise ServiceError(
                "Cannot call function '%s' on a null service" % function)

        # doing this to remove pylint errors for "cannot assign result
        # of a function call where function has no return value"
        return {}
