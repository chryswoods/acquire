
from Acquire.Service import login_to_service_account, get_service_info
from Acquire.Service import create_return_value

from Acquire.ObjectStore import ObjectStore, string_to_bytes

from Acquire.Identity import UserAccount, LoginSession

from Acquire.Crypto import PublicKey


class InvalidLoginError(Exception):
    pass


def prune_expired_sessions(bucket, user_account, root, sessions, log=[]):
    """This function will scan through all open requests and
       login sessions and will prune away old, expired or otherwise
       weird sessions. It will also use the ipaddress of the source
       to rate limit or blacklist sources"""

    for name in sessions:
        key = "%s/%s" % (root, name)
        request_key = "identity/requests/%s/%s" % (name[:8], name)

        try:
            session = ObjectStore.get_object_from_json(bucket, key)
        except:
            log.append("Session %s does not exist!" % name)
            session = None

        if session:
            should_delete = False
            should_logout = False

            try:
                session = LoginSession.from_data(session)
                if session.is_approved() or session.is_suspicious():
                    if session.hours_since_creation() > user_account \
                                                            .login_timeout():
                        should_logout = True
                        should_delete = True
                else:
                    if session.hours_since_creation() > user_account \
                                                    .login_request_timeout():
                        log.append("Expired login request: %s > %s" %
                                   (session.hours_since_creation(),
                                    user_account.login_request_timeout()))
                        should_delete = True
            except Exception as e:
                # this is corrupt - delete it
                log.append("Deleting session as corrupt? %s" % str(e))
                should_delete = True

            if should_logout:
                # auto-logout expired sessions
                log.append("Auto-logging out expired session '%s'" % key)
                session.logout()
                expire_session_key = "identity/expired_sessions/%s/%s" % \
                                     (user_account.sanitised_name(),
                                      session.uuid())

                ObjectStore.set_object_from_json(bucket, expire_session_key,
                                                 session.to_data())

            # now delete any expired sessions
            if should_delete:
                log.append("Deleting expired session '%s'" % key)

                try:
                    ObjectStore.delete_object(bucket, key)
                except:
                    pass

                try:
                    ObjectStore.delete_object(bucket, request_key)
                except:
                    pass


def run(args):
    """This function will allow a user to request a new session
       that will be validated by the passed public key and public
       signing certificate. This will return a URL that the user
       must connect to to then log in and validate that request.
    """

    status = 0
    message = None
    login_url = None
    login_uid = None
    user_uid = None

    username = args["username"]
    public_key = PublicKey.from_data(args["public_key"])
    public_cert = PublicKey.from_data(args["public_certificate"])

    ip_addr = None
    hostname = None
    login_message = None

    try:
        ip_addr = args["ipaddr"]
    except:
        pass

    try:
        hostname = args["hostname"]
    except:
        pass

    try:
        login_message = args["message"]
    except:
        pass

    # generate a sanitised version of the username
    user_account = UserAccount(username)

    # Now generate a login session for this request
    login_session = LoginSession(public_key, public_cert, ip_addr,
                                 hostname, login_message)

    # now log into the central identity account to record
    # that a request to open a login session has been opened
    bucket = login_to_service_account()

    # first, make sure that the user exists...
    account_key = "identity/accounts/%s" % user_account.sanitised_name()

    try:
        existing_data = ObjectStore.get_object_from_json(bucket,
                                                         account_key)
    except:
        existing_data = None

    if existing_data is None:
        raise InvalidLoginError("There is no user with name '%s'" %
                                username)

    user_account = UserAccount.from_data(existing_data)
    user_uid = user_account.uid()

    # first, make sure that the user doens't have too many open
    # login sessions at once - this prevents denial of service
    user_session_root = "identity/sessions/%s" % user_account.sanitised_name()

    open_sessions = ObjectStore.get_all_object_names(bucket,
                                                     user_session_root)

    # take the opportunity to prune old user login sessions
    prune_expired_sessions(bucket, user_account,
                           user_session_root, open_sessions)

    # this is the key for the session in the object store
    user_session_key = "%s/%s" % (user_session_root,
                                  login_session.uuid())

    ObjectStore.set_object_from_json(bucket, user_session_key,
                                     login_session.to_data())

    # we will record a pointer to the request using the short
    # UUID. This way we can give a simple URL. If there is a clash,
    # then we will use the username provided at login to find the
    # correct request from a much smaller pool (likely < 3)
    request_key = "identity/requests/%s/%s" % (login_session.short_uuid(),
                                               login_session.uuid())

    ObjectStore.set_string_object(bucket, request_key, user_account.name())

    status = 0

    # the login URL is the URL of this identity service plus the
    # short UID of the session
    login_url = "%s/s?id=%s" % (get_service_info().service_url(),
                                login_session.short_uuid())

    login_uid = login_session.uuid()

    message = "Success: Login via %s" % login_url

    return_value = create_return_value(status, message)

    if login_uid:
        return_value["session_uid"] = login_uid

    if login_url:
        return_value["login_url"] = login_url
    else:
        return_value["login_url"] = None

    if user_uid:
        return_value["user_uid"] = user_uid

    return return_value
