
from Acquire.Service import get_this_service
from Acquire.ObjectStore import string_to_bytes


def run(args):
    """This function return the status and service info

    Args:
        args (dict): Dictionary containing challenge information

    Returns:
        dict: containing information about the service

    """

    try:
        challenge = args["challenge"]
        fingerprint = args["fingerprint"]
    except:
        challenge = None

    response = None

    if challenge:
        service = get_this_service(need_private_access=True)
        service.assert_unlocked()

        key = service.get_key(fingerprint)
        response = key.decrypt(string_to_bytes(challenge))
    else:
        service = get_this_service(need_private_access=False)

    return_value = {"service_info": service.to_data()}

    if response is not None:
        return_value["response"] = response

    return return_value
