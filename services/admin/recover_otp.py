
from Acquire.Client import Credentials
from Acquire.Service import get_this_service
from Acquire.Identity import Authorisation, UserCredentials, UserAccount


def run(args):
    """This function is called by a user to recover or reset their primary
       one-time-password secret. This is used, e.g. if a user has changed
       their phone, or if they think the secret has been compromised, or
       if they have lost the secret completely (in which case they will
       need to log in using a backup method and then call this function
       from that login)

       The user will need to pass in a validated Authorisation, meaning
       they must have a login by at least one method (e.g. a pre-approved
       device or a one-time-login requested via backup codes or via
       an admin-authorised login)
    """

    auth = Authorisation.from_data(args["authorisation"])
    creds = args["credentials"]

    try:
        reset_otp = bool(args["reset_otp"])
    except:
        reset_otp = False

    auth.verify(resource="recover_otp")
    auth.assert_once()  # remove possibility of replay attack

    identity_uid = auth.identity_uid()

    service = get_this_service(need_private_access=False)

    if service.uid() != identity_uid:
        raise PermissionError(
            "You can only reset the OTP on the identity service on "
            "which the user is registered! %s != %s" %
            (service.uid(), identity_uid))

    user_uid = auth.user_uid()
    user = UserAccount.load(user_uid=user_uid)

    creds = Credentials.from_data(data=creds, username=user.name(),
                                  short_uid=auth.short_uid())

    otp = UserCredentials.recover_otp(user_uid=user_uid,
                                      password=creds.password(),
                                      reset_otp=reset_otp)

    issuer = "%s@%s" % (service.service_type(), service.hostname())
    provisioning_uri = otp.provisioning_uri(username=user.name(),
                                            issuer=issuer)

    return_value = {}

    return_value["user_uid"] = user_uid
    return_value["provisioning_uri"] = provisioning_uri

    return return_value
