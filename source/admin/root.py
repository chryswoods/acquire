
from Acquire.Service import create_return_value
from Acquire.Service import get_service_info


def run(args):
    """This function return the status and service info"""
    status = 0
    message = None
    service = None

    service = get_service_info()

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if service:
        return_value["service_info"] = service.to_data()

    return return_value
