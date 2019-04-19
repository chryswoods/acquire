
from Acquire.Service import get_this_service


def run(args):
    """This function return the status and service info"""
    status = 0
    message = None
    service = None

    # need private access as we will sign the returned data
    service = get_this_service(need_private_access=True)
    service.assert_unlocked()

    status = 0
    message = "Success"

    return_value = {}

    if service:
        return_value["service_info"] = service.to_data()

    return return_value
