
from Acquire.Service import setup_service_account
from Acquire.Service import create_return_value, MissingServiceAccountError


def run(args):
    """This function is called to handle the initial setup of the service.
       This specifies the password you want to use, and it returns the
       provisioning_uri that you will need to generate one-time-codes
       to log in as the admin user
    """

    service_type = "accounting"

    status = 0
    message = None
    provisioning_uri = None

    try:
        username = args["username"]
    except:
        username = "admin"

    password = args["password"]
    canonical_url = args["canonical_url"]

    provisioning_uri = setup_service_account(service_type=service_type,
                                             canonical_url=canonical_url,
                                             username=username,
                                             password=password)

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)
    return_value["provisioning_uri"] = provisioning_uri

    return return_value
