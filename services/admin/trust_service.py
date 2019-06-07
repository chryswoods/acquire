
from Acquire.Service import get_checked_remote_service, trust_service
from Acquire.Crypto import PublicKey
from Acquire.Identity import Authorisation


def run(args):
    """This function return the status and service info

       Args:
            args (dict): containing data on the service we want
            to trust

       Returns:
            dict: containing status, status message and passed in args  
    
    """
    try:
        service_url = args["service_url"]
    except:
        service_url = None

    try:
        public_cert = PublicKey.from_data(args["public_certificate"])
    except:
        public_cert = None

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        authorisation = None

    if service_url is not None:
        service = get_checked_remote_service(service_url, public_cert)
    else:
        service = None

    if service is not None:
        trust_service(service, authorisation)

    return_value = {}

    return_value["args"] = args

    return return_value
