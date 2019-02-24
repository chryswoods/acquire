
from Acquire.Service import create_return_value
from Acquire.Service import get_service_account_bucket
from Acquire.Service import call_function

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes

from Acquire.Identity import Authorisation, AuthorisationError

from Acquire.Access import Request


class RequestError(Exception):
    pass


def run(args):
    """This function is used to handle requests to access resources"""

    status = 0
    message = None

    request = None
    authorisation = None

    if "request" in args:
        request = Request.from_data(args["request"])

    if "authorisation" in args:
        authorisation = Authorisation.from_data(args["authorisation"])

    if request is None:
        status = 0
        message = "No request"

    if authorisation is None:
        raise AuthorisationError(
            "You must provide a valid authorisation to make the request %s"
            % str(request))

    authorisation.verify(request.signature())

    status = 0
    message = "Request has been validated"

    return_value = create_return_value(status, message)

    return return_value
