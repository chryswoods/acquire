
import os

from Acquire.Service import login_to_service_account
from Acquire.Service import create_return_value


def run(args):
    status = 0
    message = "TEST"

    return_value = create_return_value(status, message)

    return return_value
