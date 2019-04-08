
from Acquire.Service import create_return_value
from Acquire.Service import get_this_service


def run(args):
    """This function returns the status and service info
    
    Args:
        args: unused

       Returns:
         dict: containing information about the service
    
    """
    status = 0
    message = None
    service = None

    # need private access as we will sign the returned data
    service = get_this_service(need_private_access=True)
    service.assert_unlocked()

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if service:
        return_value["service_info"] = service.to_data()

    return return_value
