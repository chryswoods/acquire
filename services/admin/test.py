
import os

from Acquire.Service import get_this_service


def run(args):
    service = get_this_service(need_private_access=True)

    return_value = {}
    return_value["service"] = service.to_data()

    return return_value
