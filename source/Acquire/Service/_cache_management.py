
__all__ = ["clear_service_cache"]


def clear_service_cache():
    """Call this function to clear the cache of the current service.
       This is only really needed for testhing, when a single python
       interpreter will move between multiple (cached) services
    """
    from ._get_services import clear_services_cache
    from ._service_account import clear_serviceinfo_cache
    from ._login_to_objstore import clear_login_cache

    clear_services_cache()
    clear_login_cache()
    clear_serviceinfo_cache()
