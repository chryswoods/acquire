
import datetime as _datetime

from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

__all__ = ["Authorisation"]


class Authorisation:
    """This class holds the information needed to show that a user
       has authorised an action. This contains a signed token that
       records the time that the authorisation that was signed, together
       with an extra key (or secret) that can be used by the user
       and provider to verify that the authorisation is for the
       correct resource
    """
    def __init__(self, resource=None, user=None, testing_key=None):
        """Create an authorisation for the passed resource
           that is authorised by the passed user (who must be authenticated)

           If testing_key is passed, then this authorisation is being
           tested as part of the unit tests
        """

        if resource is not None:
            resource = str(resource)

        self._signature = None
        self._last_validated_time = None

        if resource is not None:
            if user is None and testing_key is None:
                raise ValueError(
                    "You must pass in an authenticated user who will "
                    "provide authorisation for resource '%s'" % resource)

        if user is not None:
            from Acquire.Client import User as _User

            if not isinstance(user, _User):
                raise TypeError("The passed user must be of type User")

            elif not user.is_logged_in():
                raise PermissionError(
                    "The passed user '%s' must be authenticated to enable "
                    "you to generate an authorisation for the account")

            self._user_uid = user.uid()
            self._session_uid = user.session_uid()
            self._identity_url = user.identity_service().canonical_url()
            self._identity_uid = user.identity_service_uid()
            self._auth_timestamp = _datetime.datetime.now().timestamp()

            message = self._get_message(resource)
            self._signature = user.signing_key().sign(message)

            self._last_validated_time = _datetime.datetime.now()
            self._last_verified_resource = resource
            self._last_verified_key = None

        elif testing_key is not None:
            self._user_uid = "some user uid"
            self._session_uid = "some session uid"
            self._identity_url = "some identity_url"
            self._identity_uid = "some identity uid"
            self._auth_timestamp = _datetime.datetime.now().timestamp()
            self._is_testing = True

            message = self._get_message(resource)
            self._signature = testing_key.sign(message)

            self._last_validated_time = _datetime.datetime.now()
            self._last_verified_resource = resource
            self._last_verified_key = testing_key.public_key()

    def is_null(self):
        """Return whether or not this authorisation is null"""
        return self._signature is None

    def _get_message(self, resource=None):
        """Internal function that is used to generate the message for
           the resource that is signed. This message
           encodes information about the user and identity service that
           signed the message, as well as the resource. This helps
           prevent tamporing with the data in this authorisation
        """
        if resource is None:
            return "%s|%s|%s|%s" % (self._user_uid, self._session_uid,
                                    self._identity_uid, self._auth_timestamp)
        else:
            return "%s|%s|%s|%s|%s" % (self._user_uid, self._session_uid,
                                       self._identity_uid, str(resource),
                                       self._auth_timestamp)

    def __str__(self):
        try:
            return "Authorisation(signature=%s)" % self._signature
        except:
            return "Authorisation()"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._signature == other._signature
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def _fix_integer(self, value, max_value):
        max_value = int(max_value)

        if value is None:
            return max_value
        else:
            try:
                value = int(value)
            except:
                return max_value

        if value <= 0 or value > max_value:
            return max_value
        else:
            return value

    def from_user(self, user_uid, service_uid):
        """Return whether or not this authorisation comes from the user
           with passed user_uid registered on the passed service_uid
        """
        return (user_uid == self._user_uid) and \
               (service_uid == self._identity_uid)

    def user_uid(self):
        """Return the UID of the user who created this authorisation"""
        if self.is_null():
            return None
        else:
            return self._user_uid

    def session_uid(self):
        """Return the login session that authenticated the user"""
        if self.is_null():
            return None
        else:
            return self._session_uid

    def identity_url(self):
        """Return the URL of the identity service that authenticated
           the user
        """
        if self.is_null():
            return None
        else:
            return self._identity_url

    def identity_uid(self):
        """Return the UID of the identity service that authenticated
           the user
        """
        if self.is_null():
            return None
        else:
            return self._identity_uid

    def signature_time(self):
        """Return the time when the authentication was signed"""
        if self.is_null():
            return None
        else:
            return _datetime.datetime.fromtimestamp(self._auth_timestamp)

    def last_verification_time(self):
        """Return the last time this authorisation was verified. Note that
           you should re-verify authorisations periodically, to ensure that
           they identity service is still happy that the login session was
           not suspicious
        """
        if self.is_null():
            return None
        else:
            return self._last_validated_time

    def signature(self):
        """Return the actual signature"""
        if self.is_null():
            return None
        else:
            return self._signature

    def is_stale(self, stale_time=7200):
        """Return whether or not this authorisation is stale.
           'stale_time' is the number of seconds after which
           the authorisation is considered stale (and thus
           no longer valid)
        """
        stale_time = self._fix_integer(stale_time, 365*24*7200)

        now = _datetime.datetime.now()

        return ((now -
                _datetime.datetime.fromtimestamp(
                    self._auth_timestamp)).seconds > stale_time)

    def is_verified(self, refresh_time=3600, stale_time=7200,
                    resource=None, testing_key=None):
        """Return whether or not this authorisation has been verified. Note
           that this will cache any verification for 'refresh_time' (in
           seconds), but re-verification can be forced if 'force' is True.

           'stale_time' gives the time (in seconds) beyond which the
           authorisation will be considered stale (and thus not valid).
           By default this is 7200 seconds (2 hours), meaning that the
           authorisation must be used within 2 hours to be valid.
        """
        refresh_time = self._fix_integer(refresh_time, 24*3600)

        now = _datetime.datetime.now()

        if self._last_validated_time is not None:
            if self._last_verified_resource != resource:
                return False

            if self._last_verified_key != testing_key:
                return False

            if (now - self._last_validated_time).seconds < refresh_time:
                # no need to re-validate
                return not self.is_stale(stale_time)

        return False

    def verify(self, resource=None, refresh_time=3600, stale_time=7200,
               force=False, testing_key=None):
        """Verify that this is a valid authorisation provided by the
           user for the passed 'resource'. This will
           cache the verification for 'refresh_time' (in seconds), but
           re-verification can be forced if 'force' is True.

           'stale_time' gives the time (in seconds) beyond which the
           authorisation will be considered stale (and thus not valid).
           By default this is 7200 seconds (2 hours), meaning that the
           authorisation must be used within 2 hours to be valid.

           If 'testing_key' is passed, then this object is being
           tested as part of the unit tests
        """

        if self.is_null():
            raise PermissionError("Cannot verify a null Authorisation")

        if self.is_stale(stale_time):
            raise PermissionError("Cannot verify a stale Authorisation")

        if not force:
            if self.is_verified(refresh_time=refresh_time,
                                stale_time=stale_time,
                                resource=resource,
                                testing_key=testing_key):
                return

        if testing_key is not None:
            if not self._is_testing:
                raise PermissionError(
                    "You cannot pass a test key to a non-testing "
                    "Authorisation")

            message = self._get_message(resource)

            try:
                testing_key.verify(self._signature, message)
            except Exception as e:
                raise PermissionError(str(e))

            self._last_validated_time = _datetime.datetime.now()
            self._last_verified_resource = resource
            self._last_verified_key = testing_key
            return

        try:
            # we need to get the public signing key for this session
            from Acquire.Service import get_trusted_service_info as \
                _get_trusted_service_info

            identity_service = _get_trusted_service_info(self._identity_url)

            if not identity_service.is_identity_service():
                raise PermissionError(
                    "Cannot verify an Authorisation that does not use a valid "
                    "identity service")

            if identity_service.uid() != self._identity_uid:
                raise PermissionError(
                    "Cannot verify this Authorisation as the actual UID of "
                    "the identity service at '%s' (%s) does not match "
                    "the UID of the service that signed this authorisation "
                    "(%s)" % (self._identity_url, identity_service.uid(),
                              self._identity_uid))

            response = identity_service.whois(
                                    user_uid=self._user_uid,
                                    session_uid=self._session_uid)

            try:
                logout_timestamp = response["logout_timestamp"]
            except:
                logout_timestamp = None

            if logout_timestamp:
                # the user has logged out from this session - ensure that
                # the authorisation was created before the user logged out
                logout_time = _datetime.datetime.fromtimestamp(
                                                        logout_timestamp)

                if logout_time < self.signature_time():
                    raise PermissionError(
                        "This authorisation was signed after the user logged "
                        "out. This means that the authorisation is not valid. "
                        "Please log in again and create a new authorisation.")

            message = self._get_message(resource)

            response["public_cert"].verify(self._signature, message)

            self._last_validated_time = _datetime.datetime.now()
            self._last_verified_resource = resource
            self._last_verified_key = None
        except PermissionError:
            raise
        except Exception as e:
            if resource:
                raise PermissionError(
                    "Cannot verify the authorisation for resource %s: %s" %
                    (resource, str(e)))
            else:
                raise PermissionError(
                    "Cannot verify the authorisation: %s" %
                    (str(e)))
        except:
            if resource:
                raise PermissionError(
                    "Cannot verify the authorisation for resource %s" %
                    resource)
            else:
                raise PermissionError("Cannot verify the authorisation")

    @staticmethod
    def from_data(data):
        """Return an authorisation created from the json-decoded dictionary"""
        auth = Authorisation()

        if (data and len(data) > 0):
            auth._user_uid = data["user_uid"]
            auth._session_uid = data["session_uid"]
            auth._identity_url = data["identity_url"]
            auth._identity_uid = data["identity_uid"]
            auth._auth_timestamp = data["auth_timestamp"]
            auth._signature = _string_to_bytes(data["signature"])
            auth._last_validated_time = None

            if "is_testing" in data:
                auth._is_testing = data["is_testing"]

        return auth

    def to_data(self):
        """Return this object serialised to a json-encoded dictionary"""
        data = {}

        if self.is_null():
            return data

        data["user_uid"] = str(self._user_uid)
        data["session_uid"] = str(self._session_uid)
        data["identity_url"] = str(self._identity_url)
        data["identity_uid"] = str(self._identity_uid)
        data["auth_timestamp"] = self._auth_timestamp
        data["signature"] = _bytes_to_string(self._signature)

        try:
            data["is_testing"] = self._is_testing
        except:
            pass

        return data
