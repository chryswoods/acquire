
__all__ = ["clear_service_cache"]


def clear_service_cache():
    """Call this function to clear the cache of the current service.
       This is only really needed for testhing, when a single python
       interpreter will move between multiple (cached) services
    """
    from ._get_services import _cache as _get_services_cache
    from ._service_account import _cache1 as _service_account_cache1
    from ._service_account import _cache2 as _service_account_cache2
    from ._login_to_objstore import _cache as _login_to_objstore_cache

    _get_services_cache.clear()
    _service_account_cache1.clear()
    _service_account_cache2.clear()
    _login_to_objstore_cache.clear()
