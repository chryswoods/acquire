
from Acquire.Service import get_service_account_bucket
from Acquire.Service import create_return_value

from Acquire.ObjectStore import ObjectStore, datetime_to_string

from Acquire.Identity import UserAccount, LoginSession


class WhoisLookupError(Exception):
    pass


class InvalidSessionError(Exception):
    pass


def run(args):
    """This function will allow anyone to query who matches
       the passed UID or username (map from one to the other)"""

    status = 0
    message = None
    user_uid = None
    username = None
    public_key = None
    public_cert = None
    logout_datetime = None
    login_status = None

    try:
        user_uid = args["user_uid"]
    except:
        pass

    try:
        username = args["username"]
    except:
        pass

    try:
        session_uid = args["session_uid"]
    except:
        session_uid = None

    bucket = None
    user_account = None

    if user_uid is None and username is None:
        raise WhoisLookupError(
            "You must supply either a username or user_uid to look up...")

    elif user_uid is None:
        # look up the user_uid from the username
        user_account = UserAccount(username)
        bucket = get_service_account_bucket()
        user_key = "identity/accounts/%s" % user_account.sanitised_name()

        try:
            user_account = UserAccount.from_data(
                                ObjectStore.get_object_from_json(bucket,
                                                                 user_key))
        except:
            raise WhoisLookupError(
                "Cannot find an account for name '%s'" % username)

        user_uid = user_account.uid()

    elif username is None:
        # look up the username from the uuid
        bucket = get_service_account_bucket()

        uid_key = "identity/whois/%s" % user_uid

        try:
            username = ObjectStore.get_string_object(bucket, uid_key)
        except:
            raise WhoisLookupError(
                "Cannot find an account for user_uid '%s'" % user_uid)

    else:
        raise WhoisLookupError(
            "You must only supply one of the username "
            "or user_uid to look up - not both!")

    if session_uid:
        # now look up the public signing key for this session, if it is
        # a valid login session
        if user_account is None:
            user_account = UserAccount(username)

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

        if login_session.is_approved():
            public_key = login_session.public_key()
            public_cert = login_session.public_certificate()

        elif login_session.is_logged_out():
            public_cert = login_session.public_certificate()
            logout_datetime = login_session.logout_time()

        else:
            raise InvalidSessionError(
                    "You cannot get the keys for a session "
                    "for which the user has not logged in!")

        login_status = login_session.status()

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if user_uid:
        return_value["user_uid"] = str(user_uid)

    if username:
        return_value["username"] = str(username)

    if public_key:
        return_value["public_key"] = public_key.to_data()

    if public_cert:
        return_value["public_cert"] = public_cert.to_data()

    if logout_datetime:
        return_value["logout_datetime"] = datetime_to_string(logout_datetime)

    if login_status:
        return_value["login_status"] = str(login_status)

    return return_value
