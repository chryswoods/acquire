
import os as _os

from enum import Enum as _Enum

from datetime import datetime as _datetime
import time as _time

from Acquire.Service import call_function as _call_function
from Acquire.Service import Service as _Service

from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import PublicKey as _PublicKey

from ._qrcode import create_qrcode as _create_qrcode
from ._qrcode import has_qrcode as _has_qrcode

from ._errors import UserError, LoginError

# If we can, import socket to get the hostname and IP address
try:
    import socket as _socket
    _has_socket = True
except:
    _has_socket = False

__all__ = ["User", "username_to_uid", "uid_to_username", "get_session_keys"]


class _LoginStatus(_Enum):
    EMPTY = 0
    LOGGING_IN = 1
    LOGGED_IN = 2
    LOGGED_OUT = 3
    ERROR = 4


def _get_identity_url():
    """Function to discover and return the default identity url"""
    return "http://130.61.60.88:8080/t/identity"


def _get_identity_service(identity_url=None):
    """Function to return the identity service for the system"""
    if identity_url is None:
        identity_url = _get_identity_url()

    privkey = _PrivateKey()
    response = _call_function(identity_url, response_key=privkey)

    try:
        service = _Service.from_data(response["service_info"])
    except:
        raise LoginError("Have not received the identity service info from "
                         "the identity service at '%s' - got '%s'" %
                         (identity_url, response))

    if not service.is_identity_service():
        raise LoginError(
            "You can only use a valid identity service to log in! "
            "The service at '%s' is a '%s'" %
            (identity_url, service.service_type()))

    if identity_url != service.service_url():
        service.update_service_url(identity_url)

    return service


def uid_to_username(user_uid, identity_url=None):
    """Function to return the username for the passed uid"""
    if identity_url is None:
        identity_url = _get_identity_url()

    response = _call_function(identity_url, "whois",
                              user_uid=str(user_uid))

    return response["username"]


def username_to_uid(username, identity_url=None):
    """Function to return the uid for the passed username"""
    if identity_url is None:
        identity_url = _get_identity_url()

    response = _call_function(identity_url, "whois",
                              username=str(username))

    return response["user_uid"]


def get_session_keys(username=None, user_uid=None, session_uid=None,
                     identity_url=None):
    """Function to return the session keys for the specified user"""
    if username is None and user_uid is None:
        raise ValueError("You must supply either the username or user_uid!")

    if session_uid is None:
        raise ValueError("You must supply a valid UID for a login session")

    if identity_url is None:
        identity_url = _get_identity_url()

    response = _call_function(identity_url, "whois",
                              username=username,
                              user_uid=user_uid,
                              session_uid=session_uid)

    try:
        response["public_key"] = _PublicKey.from_data(response["public_key"])
    except:
        pass

    try:
        response["public_cert"] = _PublicKey.from_data(response["public_cert"])
    except:
        pass

    return response


class User:
    """This class holds all functionality that would be used
       by a user to authenticate with and access the service.
       This represents a single client login, and is the
       user-facing part of Acquire
    """
    def __init__(self, username, identity_url=None):
        """Construct a null user"""
        self._username = username
        self._status = _LoginStatus.EMPTY
        self._identity_service = None

        if identity_url:
            self._identity_url = identity_url

        self._user_uid = None

    def __str__(self):
        return "User(name='%s', status=%s)" % (self.username(), self.status())

    def __enter__(self):
        """Enter function used by 'with' statements'"""
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        """Ensure that we logout"""
        self.logout()

    def __del__(self):
        """Make sure that we log out before deleting this object"""
        self.logout()

    def _set_status(self, status):
        """Internal function used to set the status from the
           string obtained from the LoginSession"""

        if status == "approved":
            self._status = _LoginStatus.LOGGED_IN
        elif status == "denied":
            self._set_error_state("Permission to log in was denied!")
        elif status == "logged_out":
            self._status = _LoginStatus.LOGGED_OUT

    def username(self):
        """Return the username of the user"""
        return self._username

    def uid(self):
        """Return the UID of this user. This uniquely identifies the
           user across all systems
        """
        if self._user_uid is None:
            self._user_uid = username_to_uid(self.username(),
                                             self.identity_service_url())
        return self._user_uid

    def status(self):
        """Return the current status of this user"""
        return self._status

    def _check_for_error(self):
        """Call to ensure that this object is not in an error
           state. If it is in an error state then raise an
           exception"""
        if self._status == _LoginStatus.ERROR:
            raise LoginError(self._error_string)

    def _set_error_state(self, message):
        """Put this object into an error state, displaying the
           passed message if anyone tries to use this object"""
        self._status = _LoginStatus.ERROR
        self._error_string = message

    def session_key(self):
        """Return the session key for the current login session"""
        self._check_for_error()

        try:
            return self._session_key
        except:
            return None

    def signing_key(self):
        """Return the signing key used for the current login session"""
        self._check_for_error()

        try:
            return self._signing_key
        except:
            return None

    def identity_service(self):
        """Return the identity service info object for the identity
           service used to validate the identity of this user
        """
        if self._identity_service:
            return self._identity_service

        self._identity_service = _get_identity_service(
                                    self.identity_service_url())

        return self._identity_service

    def identity_service_url(self):
        """Return the URL to the identity service. This is the full URL
           to the service, minus the actual function to be called, e.g.
           https://function_service.com/t/identity
        """
        self._check_for_error()

        try:
            return self._identity_url
        except:
            # return the default URL - this should be discovered...
            return _get_identity_url()

    def login_url(self):
        """Return the URL that the user must connect to to authenticate
           this login session"""
        self._check_for_error()

        try:
            return self._login_url
        except:
            return None

    def login_qr_code(self):
        """Return a QR code of the login URL that the user must connect to
           to authenticate this login session"""
        self._check_for_error()

        try:
            return self._login_qrcode
        except:
            return None

    def session_uid(self):
        """Return the UID of the current login session. Returns None
           if there is no valid login session"""
        self._check_for_error()

        try:
            return self._session_uid
        except:
            return None

    def is_empty(self):
        """Return whether or not this is an empty login (so has not
           been used for anything yet..."""
        return self._status == _LoginStatus.EMPTY

    def is_logged_in(self):
        """Return whether or not the user has successfully logged in"""
        return self._status == _LoginStatus.LOGGED_IN

    def is_logging_in(self):
        """Return whether or not the user is in the process of loggin in"""
        return self._status == _LoginStatus.LOGGING_IN

    def logout(self):
        """Log out from the current session"""
        if self.is_logged_in() or self.is_logging_in():
            identity_url = self.identity_service_url()

            if identity_url is None:
                return

            # create a permission message that can be signed
            # and then validated by the user
            permission = "Log out request for %s" % self._session_uid
            signature = self.signing_key().sign(permission)

            print("Logging out %s from session %s" % (self._username,
                                                      self._session_uid))

            result = _call_function(
                            identity_url, "logout",
                            args_key=self.identity_service().public_key(),
                            username=self._username,
                            session_uid=self._session_uid,
                            permission=permission,
                            signature=_bytes_to_string(signature))
            print(result)

            self._status = _LoginStatus.LOGGED_OUT

            return result

    def register(self, password, identity_url=None):
        """Request to register this user with the identity service running
           at 'identity_url', using the supplied 'password'. This will
           return a QR code that you must use immediately to add this
           user on the identity service to a QR code generator"""

        if self._username is None:
            return None

        if identity_url is None:
            identity_url = _get_identity_url()

        privkey = _PrivateKey()

        result = _call_function(
                    identity_url, "register",
                    args_key=self.identity_service().public_key(),
                    response_key=privkey,
                    public_cert=self.identity_service().public_certificate(),
                    username=self._username, password=password)

        try:
            provisioning_uri = result["provisioning_uri"]
        except:
            raise UserError(
                "Cannot register the user '%s' on "
                "the identity service at '%s'!" %
                (self._username, identity_url))

        # return a QR code for the provisioning URI
        return (provisioning_uri, _create_qrcode(provisioning_uri))

    def request_login(self, login_message=None):
        """Request to authenticate as this user. This returns a login URL that
           you must connect to to supply your login credentials

           If 'login_message' is supplied, then this is passed to
           the identity service so that it can be displayed
           when the user accesses the login page. This helps
           the user validate that they have accessed the correct
           login page. Note that if the message is None,
           then a random message will be generated.
        """
        self._check_for_error()

        if not self.is_empty():
            raise LoginError("You cannot try to log in twice using the same "
                             "User object. Create another object if you want "
                             "to try to log in again.")

        # first, create a private key that will be used
        # to sign all requests and identify this login
        session_key = _PrivateKey()
        signing_key = _PrivateKey()

        args = {"username": self._username,
                "public_key": session_key.public_key().to_data(),
                "public_certificate": signing_key.public_key().to_data(),
                "ipaddr": None}

        # get information from the local machine to help
        # the user validate that the login details are correct
        if _has_socket:
            hostname = _socket.gethostname()
            ipaddr = _socket.gethostbyname(hostname)
            args["ipaddr"] = ipaddr
            args["hostname"] = hostname

        if login_message is None:
            login_message = "User '%s' in process '%s' wants to log in..." % \
                              (_os.getlogin(), _os.getpid())

        args["message"] = login_message

        result = _call_function(
            self.identity_service_url(), "request_login",
            args_key=self.identity_service().public_key(),
            response_key=session_key,
            public_cert=self.identity_service().public_certificate(),
            username=self._username,
            public_key=session_key.public_key().to_data(),
            public_certificate=signing_key.public_key().to_data(),
            ipaddr=None,
            message=login_message)

        # look for status = 0
        try:
            status = int(result["status"])
        except:
            status = -1

        try:
            message = result["message"]
        except:
            message = str(result)

        try:
            prune_message = result["prune_message"]
            print("Pruning old sessions...\n%s" % "\n".join(prune_message))
        except:
            pass

        if status != 0:
            error = "Failed to login. Error = %d. Message = %s" % \
                                (status, message)
            self._set_error_state(error)
            raise LoginError(error)

        try:
            login_url = result["login_url"]
        except:
            login_url = None

        if login_url is None:
            error = "Failed to login. Could not extract the login URL! " \
                    "Result is %s" % (str(result))
            self._set_error_state(error)
            raise LoginError(error)

        try:
            session_uid = result["session_uid"]
        except:
            session_uid = None

        if session_uid is None:
            error = "Failed to login. Could not extract the login " \
                    "session UID! Result is %s" % (str(result))

            self._set_error_state(error)
            raise LoginError(error)

        # now save all of the needed data
        self._login_url = result["login_url"]
        self._session_key = session_key
        self._signing_key = signing_key
        self._session_uid = session_uid
        self._status = _LoginStatus.LOGGING_IN
        self._user_uid = result["user_uid"]

        qrcode = None

        if _has_qrcode():
            try:
                self._login_qrcode = _create_qrcode(self._login_url)
                qrcode = self._login_qrcode
            except:
                pass

        return (self._login_url, qrcode)

    def _poll_session_status(self):
        """Function used to query the identity service for this session
           to poll for the session status"""

        identity_url = self.identity_service_url()

        if identity_url is None:
            return

        result = _call_function(identity_url, "get_status",
                                username=self._username,
                                session_uid=self._session_uid)

        # look for status = 0
        try:
            status = int(result["status"])
        except:
            status = -1

        try:
            message = result["message"]
        except:
            message = str(result)

        if status != 0:
            error = "Failed to query identity service. Error = %d. " \
                    "Message = %s" % (status, message)
            self._set_error_state(error)
            raise LoginError(error)

        # now update the status...
        status = result["session_status"]
        self._set_status(status)

    def wait_for_login(self, timeout=None, polling_delta=5):
        """Block until the user has logged in. If 'timeout' is set
           then we will wait for a maximum of that number of seconds

           This will check whether we have logged in by polling
           the identity service every 'polling_delta' seconds.
        """

        self._check_for_error()

        if not self.is_logging_in():
            return self.is_logged_in()

        polling_delta = int(polling_delta)
        if polling_delta > 60:
            polling_delta = 60
        elif polling_delta < 1:
            polling_delta = 1

        if timeout is None:
            # block forever....
            while True:
                self._poll_session_status()

                if self.is_logged_in():
                    return True

                elif not self.is_logging_in():
                    return False

                _time.sleep(polling_delta)
        else:
            # only block until the timeout has been reached
            timeout = int(timeout)
            if timeout < 1:
                timeout = 1

            start_time = _datetime.now()

            while (_datetime.now() - start_time).seconds < timeout:
                self._poll_session_status()

                if self.is_logged_in():
                    return True

                elif not self.is_logging_in():
                    return False

                _time.sleep(polling_delta)

            return False
