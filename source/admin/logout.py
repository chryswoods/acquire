
from Acquire.Service import create_return_value
from Acquire.Service import login_to_service_account

from Acquire.Identity import UserAccount, LoginSession

from Acquire.ObjectStore import ObjectStore, string_to_bytes

from Acquire.Crypto import PublicKey


class InvalidSessionError(Exception):
    pass


def run(args):
    """This function will allow the current user to authorise
       a logout from the current session - this will be authorised
       by signing the request to logout"""

    status = 0
    message = None

    session_uid = args["session_uid"]
    username = args["username"]
    permission = args["permission"]
    signature = string_to_bytes(args["signature"])

    # generate a sanitised version of the username
    user_account = UserAccount(username)

    # now log into the central identity account to query
    # the current status of this login session
    bucket = login_to_service_account()

    user_session_key = "sessions/%s/%s" % \
        (user_account.sanitised_name(), session_uid)

    request_session_key = "requests/%s/%s" % (session_uid[:8], session_uid)

    login_session = LoginSession.from_data(
                        ObjectStore.get_object_from_json(bucket,
                                                         user_session_key))

    if login_session:
        # get the signing certificate from the login session and
        # validate that the permission object has been signed by
        # the user requesting the logout
        cert = login_session.public_certificate()

        cert.verify(signature, permission)

        # the signature was correct, so log the user out. For record
        # keeping purposes we change the loginsession to a logout state
        # and move it to another part of the object store
        if login_session.is_approved():
            login_session.logout()

    # only save sessions that were successfully approved
    if login_session:
        if login_session.is_logged_out():
            expired_session_key = "expired_sessions/%s/%s" % \
                                    (user_account.sanitised_name(),
                                     session_uid)

            ObjectStore.set_object_from_json(bucket, expired_session_key,
                                             login_session.to_data())

    try:
        ObjectStore.delete_object(bucket, user_session_key)
    except:
        pass

    try:
        ObjectStore.delete_object(bucket, request_session_key)
    except:
        pass

    status = 0
    message = "Successfully logged out"

    return_value = create_return_value(status, message)

    return return_value
