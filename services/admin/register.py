
from Acquire.Service import create_return_value, get_this_service
from Acquire.Identity import UserAccount


def run(args):
    """This function will allow a user to register an account with a
       username and password"""

    username = args["username"]
    password = args["password"]

    service = get_this_service(need_private_access=False)
    issuer = "%s@%s" % (service.service_type(), service.hostname())

    (user_uid, otp) = UserAccount.create(username=username,
                                         password=password)

    provisioning_uri = otp.provisioning_uri(username=username, issuer=issuer)

    return_value = create_return_value()

    return_value["user_uid"] = user_uid
    return_value["provisioning_uri"] = provisioning_uri

    return return_value
