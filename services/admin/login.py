
from Acquire.Service import get_this_service

from Acquire.Client import Credentials

from Acquire.Identity import UserAccount, LoginSession


def run(args):
    """This function is called by the user to log in and validate
       that a session is authorised to connect

       Args:
        args (dict): contains identifying information about the user,
                     short_UID, username, password and OTP code
    
        Returns:
            dict: contains a URI and a UID for this login
    """
    short_uid = args["short_uid"]
    packed_credentials = args["credentials"]

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
    sessions = LoginSession.load(short_uid=short_uid, status="pending")

    if isinstance(sessions, LoginSession):
        # we have many sessions to test...
        sessions = [sessions]

    result = None
    login_session = None
    last_error = None
    credentials = None

    for session in sessions:
        try:
            if credentials is None:
                credentials = Credentials.from_data(
                                    data=packed_credentials,
                                    username=session.username(),
                                    short_uid=short_uid)
            else:
                credentials.assert_matching_username(session.username())

            result = UserAccount.login(credentials=credentials,
                                       user_uid=user_uid,
                                       remember_device=remember_device)
            login_session = session

            # success!
            break
        except Exception as e:
            last_error = e

    if result is None or login_session is None:
        # no valid logins
        raise last_error

    # we've successfully logged in
    login_session.set_approved(user_uid=result["user"].uid(),
                               device_uid=result["device_uid"])

    return_value = {}

    return_value["user_uid"] = login_session.user_uid()

    if remember_device:
        try:
            service = get_this_service(need_private_access=False)
            hostname = service.hostname()
            if hostname is None:
                hostname = "acquire"
            issuer = "%s@%s" % (service.service_type(), hostname)
            username = result["user"].name()
            device_uid = result["device_uid"]

            otp = result["otp"]
            provisioning_uri = otp.provisioning_uri(username=username,
                                                    issuer=issuer)

            return_value["provisioning_uri"] = provisioning_uri
            return_value["otpsecret"] = otp.secret()
            return_value["device_uid"] = device_uid
        except:
            pass

    return return_value
