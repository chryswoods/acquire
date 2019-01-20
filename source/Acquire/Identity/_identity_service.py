
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

    def _call_local_function(self, function, args):
        """Internal function called to short-cut local 'remote'
           function calls
        """
        from identity.route import identity_functions as _identity_functions
        from admin.handler import create_handler as _create_handler
        handler = _create_handler(_identity_functions)
        return handler(function, args)
