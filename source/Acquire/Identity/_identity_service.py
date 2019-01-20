
import uuid as _uuid
from copy import copy as _copy

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import PublicKey as _PublicKey

from Acquire.Service import call_function as _call_function
from Acquire.Service import Service as _Service
from Acquire.Service import ServiceError

from ._errors import IdentityServiceError

__all__ = ["IdentityService"]


class IdentityService(_Service):
    """This is a specialisation of Service for Identity Services"""
    def __init__(self, other=None):
        if isinstance(other, _Service):
            self.__dict__ = _copy(other.__dict__)

            if not self.is_identity_service():
                raise IdentityServiceError(
                    "Cannot construct an IdentityService from "
                    "a service which is not an identity service!")
        else:
            _Service.__init__(self)

    def whois(self, username=None, user_uid=None, session_uid=None):
        """Do a whois lookup to map from username to user_uid or
           vice versa. If 'session_uid' is provided, then also validate
           that this is a correct login session, and return also
           the public key and signing certificate for this login session.

           This should return a dictionary with the following keys
           optionally contained;

           username = name of the user
           user_uid = uid of the user
           public_key = public key for the session with uid 'session_uid'
           public_cert = public certificate for that login session
        """

        if (username is None) and (user_uid is None):
            raise IdentityServiceError(
                    "You must supply either a username "
                    "or a user's UID for a lookup")

        key = _PrivateKey()

        response = None

        if session_uid is None:
            args = {}
        else:
            args = {"session_uid": str(session_uid)}

        try:
            if username:
                args["username"] = str(username)
                response = _call_function(
                                self.service_url(), "whois",
                                public_cert=self.public_certificate(),
                                response_key=key, args=args)
                lookup_uid = response["user_uid"]
            else:
                lookup_uid = None

            if user_uid:
                args["user_uid"] = str(user_uid)
                response = _call_function(
                    self.service_url(), "whois",
                    public_cert=self.public_certificate(),
                    response_key=key, args=args)
                lookup_username = response["username"]
            else:
                lookup_username = None

        except Exception as e:
            raise IdentityServiceError("Failed whois lookup: %s" % str(e))

        if username is None:
            username = lookup_username

        elif (lookup_username is not None) and (username != lookup_username):
            raise IdentityServiceError(
                "Disagreement of the user who matches "
                "UID=%s. We think '%s', but the identity service says '%s'" %
                (user_uid, username, lookup_username))

        if user_uid is None:
            user_uid = lookup_uid

        elif (lookup_uid is not None) and (user_uid != lookup_uid):
            raise IdentityServiceError(
                    "Disagreement of the user's UID for user "
                    "'%s'. We think %s, but the identity service says %s" %
                    (username, user_uid, lookup_uid))

        result = response

        try:
            result["public_key"] = _PublicKey.from_data(
                                            response["public_key"])
        except:
            pass

        try:
            result["public_cert"] = _PublicKey.from_data(
                                            response["public_cert"])
        except:
            pass

        return result

    def _call_local_function(self, function, args):
        """Internal function called to short-cut local 'remote'
           function calls
        """
        from identity.route import identity_functions as _identity_functions
        from admin.handler import create_handler as _create_handler
        handler = _create_handler(_identity_functions)
        return handler(function, args)
