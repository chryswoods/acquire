
from Acquire.Service import login_to_service_account
from Acquire.Service import create_return_value

from Acquire.ObjectStore import ObjectStore

from Acquire.Identity import UserAccount, LoginSession


class InvalidSessionError(Exception):
    pass


def run(args):
    """This function will allow anyone to query the current login
       status of the session with passed UID"""

    status = 0
    message = None
    session_status = None

    session_uid = args["session_uid"]
    username = args["username"]

    # generate a sanitised version of the username
    user_account = UserAccount(username)

    # now log into the central identity account to query
    # the current status of this login session
    bucket = login_to_service_account()

    user_session_key = "identity/sessions/%s/%s" % \
        (user_account.sanitised_name(), session_uid)

    try:
        login_session = LoginSession.from_data(
                            ObjectStore.get_object_from_json(
                                bucket, user_session_key))
    except:
        login_session = None

    if login_session is None:
        user_session_key = "identity/expired_sessions/%s/%s" % \
                                (user_account.sanitised_name(),
                                    session_uid)

        login_session = LoginSession.from_data(
                            ObjectStore.get_object_from_json(
                                bucket, user_session_key))

    if login_session is None:
        raise InvalidSessionError(
                "Cannot find the session '%s'" % session_uid)

    status = 0
    message = "Success: Status = %s" % login_session.status()
    session_status = login_session.status()

    return_value = create_return_value(status, message)

    if session_status:
        return_value["session_status"] = session_status

    return return_value
