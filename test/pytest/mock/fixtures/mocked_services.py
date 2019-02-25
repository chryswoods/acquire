
##########
# This file defines all of the monkey-patching and fixtures which
# are needed to run the mocked service tests
##########

import pytest
import os
import sys
import re
import uuid

import Acquire
import Acquire.Stubs

import requests as _original_requests

from admin.handler import create_handler
from identity.route import identity_functions
from accounting.route import accounting_functions
from access.route import access_functions
from storage.route import storage_functions

identity_handler = create_handler(identity_functions)
accounting_handler = create_handler(accounting_functions)
access_handler = create_handler(access_functions)
storage_handler = create_handler(storage_functions)


def _set_services(s):
    pytest.my_global_services = s


def _get_services():
    return pytest.my_global_services


class MockedRequests:
    """Mocked requests object. This provides a requests interface which calls
       the 'handler' functions of the services directly, rather
       than posting the arguments to the online services via a requests
       call. In addition, as services can call services, this also
       handles switching between the different local object stores for
       each of the services
    """
    def __init__(self, status_code, content, encoding="utf-8"):
        self.status_code = status_code
        self.content = content
        self.encoding = encoding

    @staticmethod
    def get(url, data, timeout=None):
        if url.startswith("http"):
            return _original_requests.get(url, data=data)
        else:
            return MockedRequests._perform(url, data, is_post=False)

    @staticmethod
    def post(url, data, timeout=None):
        if url.startswith("http"):
            return _original_requests.post(url, data=data)
        else:
            return MockedRequests._perform(url, data, is_post=True)

    @staticmethod
    def _perform(url, data, is_post=False):
        _services = _get_services()

        if "identity" not in _services:
            raise ValueError("NO SERVICES? %s" % str)

        from Acquire.Service import push_testing_objstore, \
            pop_testing_objstore

        if url.startswith("identity"):
            push_testing_objstore(_services["identity"])
            func = identity_handler
        elif url.startswith("access"):
            push_testing_objstore(_services["access"])
            func = access_handler
        elif url.startswith("accounting"):
            push_testing_objstore(_services["accounting"])
            func = accounting_handler
        elif url.startswith("storage"):
            push_testing_objstore(_services["storage"])
            func = storage_handler
        else:
            raise ValueError("Cannot recognise service from '%s'" % url)

        result = func(None, data)

        pop_testing_objstore()

        if type(result) is str:
            result = result.encode("utf-8")

        return MockedRequests(status_code=200, content=result)


def mocked_input(s):
    return "y"


# monkey-patch _pycurl.Curl so that we can mock calls
Acquire.Stubs.requests = MockedRequests

# monkey-patch input so that we can say "y"
Acquire.Client._wallet._input = mocked_input
Acquire.Client._wallet._is_testing = True


def _login_admin(service_url, username, password, otp):
    """Internal function used to get a valid login to the specified
       service for the passed username, password and otp
    """
    from Acquire.Client import User, Service
    from Acquire.Identity import LoginSession

    user = User(username=username, identity_url=service_url)

    user.request_login()
    short_uid = LoginSession.to_short_uid(user.session_uid())

    args = {"username": username,
            "short_uid": short_uid,
            "password": password,
            "otpcode": otp.generate()}

    service = Service(service_url)
    service.call_function(function="admin/login", args=args)

    user.wait_for_login()

    return user


@pytest.fixture(scope="session")
def aaai_services(tmpdir_factory):
    """This function creates mocked versions of all of the main services
       of the system, returning the json describing each service as
       a dictionary (which is passed to the test functions as the
       fixture)
    """
    from Acquire.Identity import Authorisation
    from Acquire.Crypto import PrivateKey, OTP
    from Acquire.Service import call_function, Service

    _services = {}
    _services["identity"] = tmpdir_factory.mktemp("identity")
    _services["accounting"] = tmpdir_factory.mktemp("accounting")
    _services["access"] = tmpdir_factory.mktemp("access")
    _services["storage"] = tmpdir_factory.mktemp("storage")
    _services["userdata"] = tmpdir_factory.mktemp("userdata")

    print("SETTING UP SERVICES: %s" % str(_services))
    _set_services(_services)

    password = PrivateKey.random_passphrase()
    args = {"password": password}

    responses = {}

    os.environ["SERVICE_PASSWORD"] = "Service_pa33word"
    os.environ["STORAGE_COMPARTMENT"] = str(_services["userdata"])

    args["canonical_url"] = "identity"
    args["service_type"] = "identity"
    response = call_function("identity", function="admin/setup", args=args)

    identity_service = Service.from_data(response["service"])
    identity_otp = OTP(OTP.extract_secret(response["provisioning_uri"]))
    identity_user = _login_admin("identity", "admin",
                                 password, identity_otp)
    responses["identity"] = {"service": identity_service,
                             "user": identity_user,
                             "response": response}

    args["canonical_url"] = "accounting"
    args["service_type"] = 'accounting'
    response = call_function("accounting",
                             function="admin/setup", args=args)
    accounting_service = Service.from_data(response["service"])
    accounting_otp = OTP(OTP.extract_secret(response["provisioning_uri"]))
    accounting_user = _login_admin("accounting", "admin", password,
                                   accounting_otp)
    responses["accounting"] = {"service": accounting_service,
                               "user": accounting_user,
                               "response": response}

    args["canonical_url"] = "access"
    args["service_type"] = "access"
    response = call_function("access", function="admin/setup", args=args)
    responses["access"] = response
    access_service = Service.from_data(response["service"])
    access_otp = OTP(OTP.extract_secret(response["provisioning_uri"]))
    access_user = _login_admin("access", "admin", password, access_otp)
    responses["access"] = {"service": access_service,
                           "user": access_user,
                           "response": response}

    args["canonical_url"] = "storage"
    args["service_type"] = "storage"
    response = call_function("storage", function="admin/setup", args=args)
    storage_service = Service.from_data(response["service"])
    storage_otp = OTP(OTP.extract_secret(response["provisioning_uri"]))
    storage_user = _login_admin("storage", "admin", password, storage_otp)
    responses["storage"] = {"service": storage_service,
                            "user": storage_user,
                            "response": response}

    resource = "trust_service %s" % identity_service.uid()
    public_cert = identity_service.public_certificate().to_data()
    args = {"service_url": identity_service.canonical_url(),
            "authorisation": Authorisation(user=accounting_user,
                                           resource=resource).to_data(),
            "public_certificate": public_cert}

    response = accounting_service.call_function(
                    function="admin/trust_service", args=args)

    args["authorisation"] = Authorisation(user=access_user,
                                          resource=resource).to_data()

    response = access_service.call_function(
                    function="admin/trust_service", args=args)

    args["authorisation"] = Authorisation(user=storage_user,
                                          resource=resource).to_data()

    response = storage_service.call_function(
                    function="admin/trust_service", args=args)

    args = {"service_url": access_service.canonical_url()}
    resource = "trust_service %s" % access_service.uid()
    args["authorisation"] = Authorisation(user=accounting_user,
                                          resource=resource).to_data()
    accounting_service.call_function(
                    function="admin/trust_service", args=args)

    args = {"service_url": accounting_service.canonical_url()}

    resource = "trust_service %s" % accounting_service.uid()
    args["authorisation"] = Authorisation(user=access_user,
                                          resource=resource).to_data()
    access_service.call_function(
                    function="admin/trust_service", args=args)

    resource = "trust_accounting_service %s" % accounting_service.uid()
    args["authorisation"] = Authorisation(user=access_user,
                                          resource=resource).to_data()
    access_service.call_function(
                    function="admin/trust_accounting_service", args=args)

    responses["_services"] = _services

    return responses


@pytest.fixture(scope="session")
def authenticated_user(aaai_services):
    from Acquire.Crypto import PrivateKey, OTP
    from Acquire.Client import User, Service

    username = str(uuid.uuid4())
    password = PrivateKey.random_passphrase()

    user = User(username, identity_url="identity")
    (provisioning_uri, _) = user.register(password)

    otpsecret = re.search(r"secret=([\w\d+]+)&issuer",
                          provisioning_uri).groups()[0]

    user_otp = OTP(otpsecret)

    # now log the user in
    (login_url, _) = user.request_login()

    assert(type(login_url) is str)

    short_uid = re.search(r"id=([\w\d+]+)",
                          login_url).groups()[0]

    args = {}
    args["short_uid"] = short_uid
    args["username"] = username
    args["password"] = password
    args["otpcode"] = user_otp.generate()

    service = Service("identity")
    result = service.call_function(function="login", args=args)

    assert(result["status"] == 0)

    user.wait_for_login()

    assert(user.is_logged_in())

    return user
