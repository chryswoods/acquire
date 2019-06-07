
from Acquire.Service import get_this_service
from Acquire.Identity import UserAccount


def run(args):
    """This function allows a user to register an account with a
       username and password
       
       Args:
        args (dict): containing the requested username and password
    
        Returns:
            dict: containing the provisioning URI
       
       """

    username = args["username"]
    password = args["password"]

    service = get_this_service(need_private_access=False)
    issuer = "%s@%s" % (service.service_type(), service.hostname())

    (user_uid, otp) = UserAccount.create(username=username,
                                         password=password)

    provisioning_uri = otp.provisioning_uri(username=username, issuer=issuer)

    return_value = {}

    return_value["user_uid"] = user_uid
    return_value["provisioning_uri"] = provisioning_uri

    return return_value
