
from Acquire.Service import create_return_value

from Acquire.Identity import LoginSession, Authorisation


def run(args):
    """This function will allow the current user to authorise
       a logout from the current session - this will be authorised
       by signing the request to logout"""

    session_uid = args["session_uid"]

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        authorisation = None

    try:
        signature = string_to_bytes(args["signature"])
    except:
        signature = None

    login_session = LoginSession.load(uid=session_uid)

    login_session.set_logged_out(authorisation=authorisation,
                                 signature=signature)

    return_value = create_return_value()

    return return_value
