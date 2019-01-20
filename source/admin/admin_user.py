
import json as _json

from cachetools import cached as _cached
from cachetools import LRUCache as _LRUCache

from Acquire.Service import get_admin_users_data as _get_admin_users_data
from Acquire.Service import get_service_info as _get_service_info
from Acquire.Service import call_function as _call_function
from Acquire.Identity import LoginSession as _LoginSession
from Acquire.Crypto import OTP as _OTP
from Acquire.Client import User as _User
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

from Acquire.Service import ServiceAccountError

__all__ = ["login_admin_user", "clear_admin_user_cache"]

_cache_admin_user = _LRUCache(maxsize=5)


def clear_admin_user_cache():
    """Clear the cache of admin user logins"""
    _cache_admin_user.clear()


@_cached(_cache_admin_user)
def login_admin_user(user_uid=None):
    """Login to the admin user account with passed user_uid. This will
       login to the first admin account if the user_uid is not supplied.
    """
    admin_users = _get_admin_users()

    if admin_users is None or len(admin_users) == 0:
        raise ServiceAccountError(
            "An admin account has not been set up for this service. Please "
            "set one up as soon as you can.")

    if user_uid is None:
        user_uid = list(admin_users.keys())[0]

    if user_uid not in admin_users:
        raise ServiceAccountError(
            "There is no admin account with UID=%s on this service."
            % user_uid)

    service = _get_service_info(need_private_access=True)
    admin_secret = _string_to_bytes(admin_users[user_uid])
    admin_secret = service.skeleton_key().decrypt(admin_secret)

    password = admin_secret["password"]
    otpsecret = admin_secret["otpsecret"]

    user = _User(user_uid=user_uid, identity_url=service.canonical_url())

    user.request_login()
    short_uid = _LoginSession.to_short_uid(user.session_uid())

    login_args = {"short_uid": short_uid,
                  "username": user.username(),
                  "password": password,
                  "otpcode": _OTP(otpsecret).generate()}

    result = _call_function(service.canonical_url(), function="login",
                            args=login_args)

    if result["status"] != 0:
        raise ServiceAccountError(
            "Error logging into the admin account: %s" % result["message"])

    user.wait_for_login()

    return user
