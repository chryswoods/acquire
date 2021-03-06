
from Acquire.Service import setup_this_service, add_admin_user
from Acquire.Service import MissingServiceAccountError

from Acquire.Crypto import OTP

from Acquire.Identity import UserAccount

from admin.register import run as register_account


def run(args):
    """This function is called to handle the initial setup of the service.
       This specifies the password you want to use, and it returns the
       provisioning_uri that you will need to generate one-time-codes
       to log in as the admin user

       Args:
            args (dict): containing data such as username, password and
            service_type requested, for setting up of the service

       Returns:
         dict: containing status of the service and provisioning URI
    """
    service_type = args["service_type"]

    try:
        username = args["username"]
    except:
        username = "admin"

    password = args["password"]
    canonical_url = args["canonical_url"]

    try:
        registry_uid = args["registry_uid"]
    except:
        registry_uid = "a0-a0"

    if username is None or password is None or service_type is None:
        raise PermissionError(
            "You need to supply more information to be able to set "
            "up this service!")

    (service, user_uid, otp) = setup_this_service(service_type=service_type,
                                                  canonical_url=canonical_url,
                                                  registry_uid=registry_uid,
                                                  username=username,
                                                  password=password)

    if user_uid is None or otp is None:
        raise PermissionError(
            "You cannot setup this service because it has already been "
            "setup and configured!")

    issuer = "%s@%s" % (service.service_type(), service.hostname())

    provisioning_uri = otp.provisioning_uri(username=username,
                                            issuer=issuer)

    return_value = {}
    return_value["service"] = service.to_data()
    return_value["provisioning_uri"] = provisioning_uri

    return return_value
