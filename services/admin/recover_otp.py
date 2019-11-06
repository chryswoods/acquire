
from Acquire.Service import get_this_service

from Acquire.Identity import Authorisation


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

    try:
        reset_otp = bool(args["reset_otp"])
    except:
        reset_otp = False

    auth.verify(resource="reset_otp")

    identity_uid = auth.identity_uid()

    service = get_this_service(need_private_access=True)

    if service.uid() != identity_uid:
        raise PermissionError(
            "You can only reset the OTP on the identity service on "
            "which the user is registered! %s != %s" %
            (service.uid(), identity_uid))

    user_uid = auth.user_uid()

    return (user_uid, reset_otp)
