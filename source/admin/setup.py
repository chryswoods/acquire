
from Acquire.Service import setup_this_service, add_admin_user
from Acquire.Service import create_return_value, MissingServiceAccountError

from Acquire.Crypto import OTP

from admin.register import run as register_account
from admin.whois import run as whois


def run(args):
    """This function is called to handle the initial setup of the service.
       This specifies the password you want to use, and it returns the
       provisioning_uri that you will need to generate one-time-codes
       to log in as the admin user
    """

    status = 0
    message = None
    provisioning_uri = None

    try:
        service_type = args["service_type"]
    except:
        service_type = None

    try:
        username = args["username"]
    except:
        username = "admin"

    try:
        password = args["password"]
    except:
        password = None

    try:
        canonical_url = args["canonical_url"]
    except:
        canonical_url = None

    service = setup_this_service(service_type=service_type,
                                 canonical_url=canonical_url)

    # now register the new user account
    register_args = {"username": username, "password": password}
    result = register_account(register_args)

    provisioning_uri = result["provisioning_uri"]

    whois_args = {"username": username}
    result = whois(whois_args)
    admin_uid = result["user_uid"]

    add_admin_user(service, admin_uid)

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)
    return_value["service"] = service.to_data()
    return_value["provisioning_uri"] = provisioning_uri

    return return_value
