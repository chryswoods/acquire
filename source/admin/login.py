
import datetime
import uuid

from Acquire.Service import login_to_service_account
from Acquire.Service import create_return_value

from Acquire.Identity import UserAccount, LoginSession

from Acquire.ObjectStore import ObjectStore, get_datetime_now, \
                                string_to_datetime, datetime_to_string


class LoginError(Exception):
    pass


def run(args):
    """This function is called by the user to log in and validate
       that a session is authorised to connect"""

    status = 0
    message = None
    provisioning_uri = None
    assigned_device_uid = None

    short_uid = args["short_uid"]
    username = args["username"]
    password = args["password"]
    otpcode = args["otpcode"]

    try:
        remember_device = args["remember_device"]
    except:
        remember_device = False

    try:
        device_uid = args["device_uid"]
    except:
        device_uid = None

    # create the user account for the user
    user_account = UserAccount(username)

    # log into the central identity account to query
    # the current status of this login session
    bucket = login_to_service_account()

    # locate the session referred to by this uid
    base_key = "identity/requests/%s" % short_uid
    session_keys = ObjectStore.get_all_object_names(bucket, base_key)
    len_base_key = len(base_key)

    # try all of the sessions to find the one that the user
    # may be referring to...
    login_session_key = None
    request_session_key = None

    for request_session_key in session_keys:
        session_user = ObjectStore.get_string_object(
                            bucket, request_session_key)

        # did the right user request this session?
        if user_account.name() == session_user:
            if login_session_key:
                # this is an extremely unlikely edge case, whereby
                # two login requests within a 30 minute interval for the
                # same user result in the same short UID. This should be
                # signified as an error and the user asked to create a
                # new request
                raise LoginError(
                    "You have found an extremely rare edge-case "
                    "whereby two different login requests have randomly "
                    "obtained the same short UID. As we can't work out "
                    "which request is valid, the login is denied. Please "
                    "create a new login request, which will then have a "
                    "new login request UID")
            else:
                login_session_key = request_session_key[len_base_key:]
                while login_session_key.startswith("/"):
                    login_session_key = login_session_key[1:]

    if not login_session_key:
        raise LoginError(
            "There is no active login request with the "
            "short UID '%s' for user '%s'" % (short_uid, username))

    _base_login_session_key = login_session_key
    login_session_key = "identity/sessions/%s/%s" % (
                            user_account.sanitised_name(),
                            login_session_key)

    # fully load the user account from the object store so that we
    # can validate the username and password
    try:
        account_key = "identity/accounts/%s" % user_account.sanitised_name()
        user_account = UserAccount.from_data(
            ObjectStore.get_object_from_json(bucket, account_key))
    except:
        raise LoginError("No account available with username '%s'" %
                         username)

    if (not remember_device) and device_uid:
        # see if this device has been seen before
        device_key = "identity/devices/%s/%s" % (user_account.sanitised_name(),
                                                 device_uid)

        try:
            device_secret = ObjectStore.get_string_object(bucket,
                                                          device_key)
        except:
            device_secret = None

        if device_secret is None:
            raise LoginError(
                "The login device is not recognised. Please try to "
                "log in again using your master one-time-password.")
    else:
        device_secret = None

    # now try to log into this account using the supplied
    # password and one-time-code
    try:
        if device_secret:
            user_account.validate_password(password, otpcode,
                                           device_secret=device_secret)
        elif remember_device:
            (device_secret, provisioning_uri) = \
                        user_account.validate_password(
                                    password, otpcode,
                                    remember_device=True)

            device_uid = str(uuid.uuid4())
            device_key = "identity/devices/%s/%s" % (
                                            user_account.sanitised_name(),
                                            device_uid)

            assigned_device_uid = device_uid
        else:
            user_account.validate_password(password, otpcode)
    except:
        # don't leak info about why validation failed
        raise LoginError("The password or OTP code is incorrect")

    # the user is valid - load up the actual login session
    login_session = LoginSession.from_data(
                        ObjectStore.get_object_from_json(bucket,
                                                         login_session_key))

    if login_session is None:
        raise LoginError("How can we have a null login session at "
                         "key '%s'\n"
                         "identity + / sessions + / %s + / %s"
                         % (login_session_key, _base_login_session_key,
                            user_account.sanitised_name()))

    # we must record the session against which this otpcode has
    # been validated. This is to stop us validating an otpcode more than
    # once (e.g. if the password and code have been intercepted).
    # Any sessions validated using the same code should be treated
    # as immediately suspcious
    otproot = "identity/otps/%s" % user_account.sanitised_name()
    sessions = ObjectStore.get_all_strings(bucket, otproot)

    utcnow = get_datetime_now()

    for session in sessions:
        otpkey = session
        otpstring = ObjectStore.get_string_object(bucket, otpkey)

        (datestring, code) = otpstring.split("|||")

        # remove all codes that are more than 10 minutes old. The
        # otp codes are only valid for 3 minutes, so no need to record
        # codes that have been used that are older than that...
        timedelta = utcnow - string_to_datetime(datestring)

        if timedelta.seconds > 600:
            try:
                ObjectStore.delete_object(bucket, otpkey)
            except:
                pass

        elif code == str(otpcode):
            # Low probability there is some recycling,
            # but very suspicious if the code was validated within the last
            # 10 minutes... (as 3 minute timeout of a code)
            suspect_key = "identity/sessions/%s/%s" % (
                user_account.sanitised_name(), session)

            suspect_session = None

            try:
                suspect_session = LoginSession.from_data(
                        ObjectStore.get_object_from_json(bucket,
                                                         suspect_key))
            except:
                pass

            if suspect_session:
                suspect_session.set_suspicious()
                ObjectStore.set_object_from_json(bucket, suspect_key,
                                                 suspect_session.to_data())

            raise LoginError(
                "Cannot authorise the login as the one-time-code "
                "you supplied has already been used within the last 10 "
                "minutes. The chance of this happening is really low, so "
                "we are treating this as a suspicious event. You need to "
                "try another code. Meanwhile, the other login that used "
                "this code has been put into a 'suspicious' state.")

    # record the value and datetime of when this otpcode was used
    otpkey = "%s/%s" % (otproot, login_session.uuid())
    otpstring = "%s|||%s" % (datetime_to_string(get_datetime_now()),
                             otpcode)

    ObjectStore.set_string_object(bucket, otpkey, otpstring)

    login_session.set_approved()

    # write this session back to the object store
    ObjectStore.set_object_from_json(bucket, login_session_key,
                                     login_session.to_data())

    # save the device secret as everything has now worked
    if assigned_device_uid:
        ObjectStore.set_string_object(bucket, device_key,
                                      device_secret)

    # finally, remove this from the list of requested logins
    try:
        ObjectStore.delete_object(bucket, request_session_key)
    except:
        pass

    status = 0
    message = "Success: Status = %s" % login_session.status()

    return_value = create_return_value(status, message)

    if provisioning_uri:
        return_value["provisioning_uri"] = provisioning_uri
        return_value["device_uid"] = assigned_device_uid

    return return_value
