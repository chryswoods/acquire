
from Acquire.Service import create_return_value

from Acquire.Identity import LoginSession, Authorisation

from Acquire.ObjectStore import string_to_bytes


def run(args):
    """This function will allow anyone to query the current login
       status of the session with passed UID
    """
    session_uid = args["session_uid"]

    login_session = LoginSession.load(uid=session_uid)

    return_value = create_return_value()

    return_value["session_status"] = login_session.status()

    try:
        return_value["user_uid"] = login_session.user_uid()
    except:
        pass

    return return_value
