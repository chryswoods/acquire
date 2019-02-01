
import json as _json

from cachetools import cached as _cached
from cachetools import LRUCache as _LRUCache

from Acquire.Identity import LoginSession as _LoginSession

from Acquire.Service import call_function as _call_function

from Acquire.Crypto import OTP as _OTP

from Acquire.Client import User as _User

__all__ = ["login_service_user", "clear_service_user_cache"]

_cache_service_user = _LRUCache(maxsize=5)


def clear_service_user_cache():
    """Clear the cache of service user logins"""
    _cache_service_user.clear()


@_cached(_cache_service_user)
def login_service_user(service_uid):
    """Login to the service user account for the service with
       UID 'service_uid'. The service user account is an
       account that provides full control for this service. The "admin"
       accounts invoke actions by logging into the service account and
       authorising actions using that account. It is not possible to
       login as the service user from outside the service. It is an
       account that is internal to the service.
    """
    from Acquire.Service import get_service_info as _get_service_info

    service = _get_service_info(need_private_access=True)

    if service.uid() != service_uid:
        from Acquire.Service import ServiceAccountError
        raise ServiceAccountError(
            "You cannot login to the service account for '%s' from "
            "the service running at '%s'" % (service.uid(),
                                             service_uid))

    secrets = service.skeleton_key().decrypt(service.service_user_secrets())
    secrets = _json.loads(secrets)

    password = secrets["password"]
    otpsecret = secrets["otpsecret"]

    user = _User(user_uid=service.service_user_uid(),
                 identity_url=service.canonical_url())

    user.request_login()
    short_uid = _LoginSession.to_short_uid(user.session_uid())

    login_args = {"short_uid": short_uid,
                  "username": user.username(),
                  "password": password,
                  "otpcode": _OTP(otpsecret).generate()}

    secrets = None

    result = _call_function(service.canonical_url(), function="login",
                            args=login_args)

    login_args = None

    if result["status"] != 0:
        from Acquire.Service import ServiceAccountError
        raise ServiceAccountError(
            "Error logging into the admin account: %s" % result["message"])

    user.wait_for_login()

    return user
