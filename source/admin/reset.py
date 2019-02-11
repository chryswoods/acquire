
import os

from Acquire.Service import get_service_info
from Acquire.Service import create_return_value


def run(args):
    """This function completely resets a service and deletes
       all data. This resets back to the original state.
       Obviously you should be really sure you want to do this!
    """

    status = 0
    message = "Resetting service..."

    return {"status": status, "message": message}
