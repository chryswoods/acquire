
from Acquire.Service import create_return_value

from Acquire.Identity import LoginSession

from Acquire.ObjectStore import datetime_to_string


def run(args):
    """This function will allow anyone to obtain the public
       keys for the passed login session
    """
    session_uid = args["session_uid"]

    try:
        scope = args["scope"]
    except:
        scope = None

    try:
        permissions = args["permissions"]
    except:
        permissions = None

    login_session = LoginSession.load(uid=session_uid, scope=scope,
                                      permissions=permissions)

    return_value = create_return_value()

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

    return_value["login_status"] = login_session.status()

    return return_value
