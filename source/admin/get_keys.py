
from Acquire.ObjectStore import ObjectStore, bytes_to_string

from Acquire.Service import create_return_value, login_to_service_account

from Acquire.Identity import UserAccount, LoginSession


class InvalidSessionError(Exception):
    pass


def run(args):
    """This function will allow anyone to obtain the public
       keys for the passed login session of a user with
       a specified login UID"""

    public_key = None
    public_cert = None
    login_status = None
    logout_timestamp = None

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

    # only send valid keys if the user had logged in!
    if login_session.is_approved():
        public_key = login_session.public_key()
        public_cert = login_session.public_certificate()

    elif login_session.is_logged_out():
        public_cert = login_session.public_certificate()
        logout_timestamp = login_session.logout_time().timestamp()

    else:
        raise InvalidSessionError(
                "You cannot get the keys for a session "
                "for which the user has not logged in!")

    login_status = login_session.status()

    status = 0
    message = "Success: Status = %s" % login_session.status()

    return_value = create_return_value(status, message)

    if public_key:
        return_value["public_key"] = public_key.to_data()

    if public_cert:
        return_value["public_cert"] = public_cert.to_data()

    if login_status:
        return_value["login_status"] = str(login_status)

    if logout_timestamp:
        return_value["logout_timestamp"] = logout_timestamp

    return return_value
