
from Acquire.Service import Service as _Service
from Acquire.Service import call_function as _call_function

from Acquire.Crypto import get_private_key as _get_private_key

__all__ = ["Service"]


class Service:
    """This class provides a client-side wrapper to fetch or set-up
       a service
    """
    def __init__(self, service_url, service_type=None):
        response_key = _get_private_key()

        if service_type is None:
            # fetch the remote service
            response = _call_function(service_url=service_url,
                                      response_key=response_key)

            service = _Service.from_data(response["service_info"])

            from copy import copy as _copy
            self.__dict__ = _copy(service.__dict__)
            self.__class__ = service.__class__
