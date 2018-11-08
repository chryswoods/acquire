
from Acquire.Service import create_return_value
from Acquire.Service import login_to_service_account
from Acquire.Service import call_function

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes

from Acquire.Access import Request


class RequestError(Exception):
    pass


def run(args):
    """This function is used to handle requests to access resources"""

    status = 0
    message = None

    access_token = None

    request = Request.from_data(args["request"])

    access_token = request.to_data()

    return_value = create_return_value(status, message)

    if access_token:
        return_value["access_token"] = access_token

    return return_value
