
import uuid as _uuid
from copy import copy as _copy

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import PublicKey as _PublicKey

from Acquire.Service import call_function as _call_function
from Acquire.Service import Service as _Service

from ._errors import AccessServiceError

__all__ = ["AccessService"]


class AccessService(_Service):
    """This is a specialisation of Service for Access Services"""
    def __init__(self, other=None):
        if isinstance(other, _Service):
            self.__dict__ = _copy(other.__dict__)

            if not self.is_access_service():
                raise AccessServiceError(
                    "Cannot construct an AccessService from "
                    "a service which is not an access service!")
        else:
            _Service.__init__(self)
