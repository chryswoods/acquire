
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

    service = get_service_info(need_private_access=False)

    return_value = create_return_value(status, message)
    return_value["service"] = service.to_data()

    return return_value
