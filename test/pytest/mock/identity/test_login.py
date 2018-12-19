
import pytest
import os
import sys
import re
import asyncio

import Acquire.Service
import Acquire.Client

from Acquire.Crypto import PrivateKey, OTP

from Acquire.Service import login_to_service_account
from Acquire.Service import _push_testing_objstore, _pop_testing_objstore
from Acquire.Service import call_function

from identity.route import handler as identity_handler
from accounting.route import handler as accounting_handler
from access.route import handler as access_handler
from storage.route import handler as storage_handler


class MockedPyCurl:
    """Mocked pycurl.PyCurl class"""
    def __init__(self):
        self._data = {}

    URL = "URL"
    WRITEDATA = "WRITEDATA"
    POSTFIELDS = "POSTFIELDS"

    def setopt(self, typ, value):
        self._data[typ] = value

    def perform(self):
        url = self._data["URL"]

        global _services

        if url.startswith("identity"):
            _push_testing_objstore(_services["identity"])
            func = identity_handler
        elif url.startswith("access"):
            _push_testing_objstore(_services["access"])
            func = access_handler
        elif url.startswith("accounting"):
            _push_testing_objstore(_services["accounting"])
            func = accounting_handler
        elif url.startswith("storage"):
            _push_testing_objstore(_services["storage"])
            func = storage_handler
        else:
            raise ValueError("Cannot recognise service from '%s'" % url)

        result = func(None, self._data["POSTFIELDS"])

        _pop_testing_objstore()

        if type(result) is str:
            result = result.encode("utf-8")

        self._data["WRITEDATA"].write(result)

    def close(self):
        pass


# monkey-patch _pycurl.Curl so that we can mock calls
Acquire.Service._function._pycurl.Curl = MockedPyCurl

_services = {}                    # global objstore for each service

@pytest.fixture(scope="module")
def aaai_services(tmpdir_factory):
    global _services
    _services["identity"] = tmpdir_factory.mktemp("identity")
    _services["accounting"] = tmpdir_factory.mktemp("accounting")
    _services["access"] = tmpdir_factory.mktemp("access")
    _services["storage"] = tmpdir_factory.mktemp("storage")

    args = {"password": "ABCdef12345"}

    responses = {}

    os.environ["SERVICE_PASSWORD"] = "Service_pa33word"

    args["service_url"] = "identity"
    response = call_function("identity", function="setup", args=args)
    responses["identity"] = response

    args["service_url"] = "accounting"
    args["new_service"] = "identity"
    response = call_function("accounting", function="setup", args=args)
    responses["accounting"] = response

    args["service_url"] = "storage"
    args["new_service"] = "identity"
    response = call_function("storage", function="setup", args=args)
    responses["storage"] = response

    args["service_url"] = "access"
    args["new_service"] = "identity"
    response = call_function("access", function="setup", args=args)
    responses["access"] = response

    return responses


def test_login(aaai_services):
    # register the new user
    username = "testuser"
    password = "ABCdef12345"

    user = Acquire.Client.User(username, identity_url="identity")

    (provisioning_uri, qrcode) = user.register(password)

    # extract the shared secret from the provisioning URI
    otpsecret = re.search(r"secret=([\w\d+]+)&issuer",
                          provisioning_uri).groups()[0]

    user_otp = OTP(otpsecret)

    # now get and check the whois lookup...
    user_uid = user.uid()
    check_username = Acquire.Client.uid_to_username(user_uid,
                                                    identity_url="identity")

    assert(check_username == username)

    (login_url, qrcode) = user.request_login()

    assert(type(login_url) is str)

    short_uid = re.search(r"id=([\w\d+]+)",
                          login_url).groups()[0]

    args = {}
    args["short_uid"] = short_uid
    args["username"] = username
    args["password"] = password
    args["otpcode"] = user_otp.generate()

    result = call_function("identity", "login", args=args)

    assert("status" in result)
    assert(result["status"] == 0)

    user.logout()
