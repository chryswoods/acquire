
from Acquire.Service import create_return_value
from Acquire.Service import get_remote_service_info
from Acquire.Crypto import PrivateKey


def run(args):
    """This function return the status and service info"""
    status = 0
    message = None

    try:
        service_url = args["service_url"]
    except:
        service_url = None

    try:
        public_cert = args["public_certificate"]
    except:
        public_cert = None

    try:
        authorisation = args["authorisation"]
    except:
        authorisation = None

    if service_url is not None:
        service = get_remote_service_info(service_url, public_cert)

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if service:
        return_value["service_info"] = service.to_data()

    return return_value
