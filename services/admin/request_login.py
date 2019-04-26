
from Acquire.Identity import LoginSession

from Acquire.Crypto import PublicKey


def run(args):
    """This function will allow a user to request a new session
       that will be validated by the passed public key and public
       signing certificate. This will return a URL that the user
       must connect to to then log in and validate that request.

        Args:
            args (dict): containing login data such as username, password etc

        Returns:
            dict: containing status of login attempt
    """
    username = args["username"]
    public_key = PublicKey.from_data(args["public_key"])
    public_cert = PublicKey.from_data(args["public_certificate"])
    scope = args["scope"]
    permissions = args["permissions"]

    try:
        hostname = args["hostname"]
    except:
        hostname = None

    try:
        ipaddr = args["ipaddr"]
    except:
        ipaddr = None

    try:
        login_message = args["login_message"]
    except:
        login_message = None

    # Generate a login session for this request
    login_session = LoginSession(username=username,
                                 public_key=public_key,
                                 public_cert=public_cert,
                                 ipaddr=ipaddr, hostname=hostname,
                                 login_message=login_message,
                                 scope=scope, permissions=permissions)

    return_value = {}

    return_value["login_url"] = login_session.login_url()
    return_value["short_uid"] = login_session.short_uid()
    return_value["session_uid"] = login_session.uid()

    return return_value
