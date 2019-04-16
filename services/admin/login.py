
from Acquire.Service import create_return_value

from Acquire.Client import Credentials

from Acquire.Identity import UserAccount, LoginSession


def run(args):
    """This function is called by the user to log in and validate
       that a session is authorised to connect
    """
    short_uid = args["short_uid"]
    credentials = Credentials.from_data(args["credentials"])

    try:
        user_uid = args["user_uid"]
    except:
        user_uid = None

    try:
        remember_device = args["remember_device"]

        if remember_device:
            remember_device = True
        else:
            remember_device = False
    except:
        remember_device = False

    # get the session referred to by the short_uid
    sessions = LoginSession.load(short_uid=short_uid)

    if isinstance(sessions, LoginSession):
        # we have many sessions to test...
        sessions = [sessions]

    result = None
    last_error = None

    for session in sessions:
        try:
            result = UserAccount.login(username=session.username(),
                                       short_uid=short_uid,
                                       credentials=credentials,
                                       user_uid=user_uid,
                                       remember_device=remember_device)

            # success!
            break
        except Exception as e:
            last_error = e

    if result is None:
        # no valid logins
        raise last_error

    # we've successfully logged in
    login_session.set_approved(result)

    return_value = create_return_value()

    return_value["user_uid"] = result["user"].uid()

    if remember_device:
        try:
            return_value["device_uid"] = result["device_uid"]
        except:
            pass

        try:
            return_value["provisioning_uri"] = otp.provisioning_uri()
        except:
            pass

    return return_value
