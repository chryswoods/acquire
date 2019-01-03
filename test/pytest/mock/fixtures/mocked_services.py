
##########
# This file defines all of the monkey-patching and fixtures which
# are needed to run the mocked service tests
##########

import pytest
import os

import Acquire.Service

from Acquire.Service import login_to_service_account
from Acquire.Service import _push_testing_objstore, _pop_testing_objstore
from Acquire.Service import call_function

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
