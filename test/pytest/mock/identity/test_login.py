
import pytest
import os
import sys
import re
import asyncio

import Acquire.Service

from Acquire.Crypto import PrivateKey, OTP
from Acquire.Identity import LoginSession

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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

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

        result = loop.run_until_complete(func(None, self._data["POSTFIELDS"]))

        _pop_testing_objstore()

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
    response = call_function("accounting", function="setup", args=args)
    responses["accounting"] = response

    return responses


def test_login(aaai_services):
    response = call_function("identity")
    print(response)
    assert(False)

    # register the new user
    username = "testuser"
    password = "ABCdef12345"

    args = {"username": username,
            "password": password}

    result = register(args)

    assert("status" in result)
    assert(result["status"] == 0)

    assert("provisioning_uri" in result)
    provisioning_uri = result["provisioning_uri"]

    # extract the shared secret from the provisioning URI
    otpsecret = re.search(r"secret=([\w\d+]+)&issuer",
                          provisioning_uri).groups()[0]

    otp = OTP(otpsecret)

    # now get and check the whois lookup...

    session_key = PrivateKey()
    session_cert = PrivateKey()

    args = {"username": "testuser",
            "public_key": session_key.public_key().to_data(),
            "public_certificate": session_cert.public_key().to_data()}

    result = request_login(args)

    assert("status" in result)
    assert(result["status"] == 0)

    assert("login_url" in result)
    login_url = result["login_url"]

    assert("session_uid" in result)
    session_uid = result["session_uid"]

    short_uid = re.search(r"id=([\w\d+]+)",
                          login_url).groups()[0]

    assert(short_uid == LoginSession.to_short_uid(session_uid))

    assert(False)
