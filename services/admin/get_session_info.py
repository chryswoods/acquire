
from Acquire.Identity import LoginSession

from Acquire.ObjectStore import datetime_to_string


def run(args):
    """This function will allow anyone to obtain the public
       keys for the passed login session
    """
    try:
        session_uid = args["session_uid"]
    except:
        session_uid = None

    try:
        short_uid = args["short_uid"]
    except:
        short_uid = None

    try:
        scope = args["scope"]
    except:
        scope = None

    try:
        permissions = args["permissions"]
    except:
        permissions = None

    if session_uid:
        login_session = LoginSession.load(uid=session_uid, scope=scope,
                                          permissions=permissions)
    else:
        if short_uid is None:
            raise PermissionError(
                "You must specify either the session_uid or the short_uid "
                "of the login session")

        try:
            status = args["status"]
        except:
            raise PermissionError(
                "You must specify the status of the short_uid session you "
                "wish to query...")

        login_session = LoginSession.load(short_uid=short_uid, status=status,
                                          scope=scope,
                                          permissions=permissions)

    return_value = {}

    # only send information if the user had logged in!
    should_return_data = False

    if login_session.is_approved():
        should_return_data = True
        return_value["public_key"] = login_session.public_key().to_data()

    elif login_session.is_logged_out():
        should_return_data = True
        return_value["logout_datetime"] = \
            datetime_to_string(login_session.logout_time())

    if should_return_data:
        return_value["public_cert"] = \
            login_session.public_certificate().to_data()
        return_value["scope"] = login_session.scope()
        return_value["permissions"] = login_session.permissions()
        return_value["user_uid"] = login_session.user_uid()

    return_value["session_status"] = login_session.status()
    return_value["login_message"] = login_session.login_message()

    return return_value
