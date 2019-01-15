
##########
# This file defines all of the monkey-patching and fixtures which
# are needed to run the mocked service tests
##########

import pytest
import os
import sys
import re
import uuid

import Acquire.Service

from Acquire.Service import login_to_service_account
from Acquire.Service import _push_testing_objstore, _pop_testing_objstore
from Acquire.Service import call_function

from Acquire.Client import User, uid_to_username
from Acquire.Crypto import OTP

from identity.route import handler as identity_handler
from accounting.route import handler as accounting_handler
from access.route import handler as access_handler
from storage.route import handler as storage_handler

try:
    from pycurl import Curl as _original_Curl
except:
    _original_Curl = None


class MockedPyCurl:
    """Mocked pycurl.PyCurl class. This provides a PyCurl which calls
       the 'handler' functions of the services directly, rather
       than posting the arguments to the online services via a curl
       call. In addition, as services can call services, this also
       handles switching between the different local object stores for
       each of the services
    """
    def __init__(self):
        self._data = {}
        self._c = _original_Curl()
        # self._c.setopt(self._c.VERBOSE, True)

    URL = "URL"
    WRITEDATA = "WRITEDATA"
    POSTFIELDS = "POSTFIELDS"
    POST = "POST"
    CUSTOMREQUEST = "CUSTOMREQUEST"

    def setopt(self, typ, value):
        self._data[typ] = value
        try:
            if typ == MockedPyCurl.URL:
                self._c.setopt(self._c.URL, value)
            elif typ == MockedPyCurl.WRITEDATA:
                self._c.setopt(self._c.WRITEDATA, value)
            elif typ == MockedPyCurl.POSTFIELDS:
                self._c.setopt(self._c.POSTFIELDS, value)
            elif typ == MockedPyCurl.POST:
                self._c.setopt(self._c.POST, value)
            elif typ == MockedPyCurl.CUSTOMREQUEST:
                self._c.setopt(self._c.CUSTOMREQUEST, value)
        except:
            pass

    def perform(self):
        url = self._data["URL"]

        if url.startswith("http"):
            self._c.perform()
            return

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

    def getinfo(self, key):
        url = self._data["URL"]

        if url.startswith("http"):
            return self._c.getinfo(key)
        else:
            return 200

    def close(self):
        try:
            self._c.close()
        except:
            pass


# monkey-patch _pycurl.Curl so that we can mock calls
Acquire.Service._function._pycurl.Curl = MockedPyCurl

_services = {}                    # global objstore for each service


@pytest.fixture(scope="module")
def aaai_services(tmpdir_factory):
    """This function creates mocked versions of all of the main services
       of the system, returning the json describing each service as
       a dictionary (which is passed to the test functions as the
       fixture)
    """
    global _services
    _services["identity"] = tmpdir_factory.mktemp("identity")
    _services["accounting"] = tmpdir_factory.mktemp("accounting")
    _services["access"] = tmpdir_factory.mktemp("access")
    _services["storage"] = tmpdir_factory.mktemp("storage")
    _services["userdata"] = tmpdir_factory.mktemp("userdata")

    args = {"password": "ABCdef12345"}

    responses = {}

    os.environ["SERVICE_PASSWORD"] = "Service_pa33word"
    os.environ["STORAGE_COMPARTMENT"] = str(_services["userdata"])

    args["service_url"] = "identity"
    response = call_function("identity", function="setup", args=args)
    responses["identity"] = response

    args["service_url"] = "accounting"
    args["new_service"] = "identity"
    response = call_function("accounting", function="setup", args=args)
    responses["accounting"] = response

    args["service_url"] = "access"
    args["new_service"] = "identity"
    response = call_function("access", function="setup", args=args)
    responses["access"] = response

    args["service_url"] = "storage"
    args["new_service"] = "identity"
    response = call_function("storage", function="setup", args=args)
    responses["storage"] = response

    responses["_services"] = _services

    return responses


@pytest.fixture(scope="module")
def authenticated_user(aaai_services):
    # register the new user
    username = str(uuid.uuid4())
    password = "RF%5s123!" % str(uuid.uuid4())[0:5]

    user = User(username, identity_url="identity")
    (provisioning_uri, qrcode) = user.register(password)

    otpsecret = re.search(r"secret=([\w\d+]+)&issuer",
                          provisioning_uri).groups()[0]

    user_otp = OTP(otpsecret)

    # now log the user in
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

    print(result)

    assert(result["status"] == 0)

    user.wait_for_login()

    assert(user.is_logged_in())

    return user
