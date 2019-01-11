
import pytest
import os

from Acquire.Access import RunRequest
from Acquire.Identity import Authorisation
from Acquire.Service import call_function


def _testdata():
    """Return the path to the directory containing test data"""
    return os.path.dirname(os.path.abspath(__file__)) + \
        os.path.sep + "example_sim"


def test_run_calc(aaai_services, authenticated_user):
    user = authenticated_user
    assert(user.is_logged_in())

    runfile = "%s/run.yaml" % _testdata()

    # create a request for this calculation and authorise
    # it using the authenticated user
    r = RunRequest(runfile=runfile)

    func = "run_calculation"
    args = {}
    args["request"] = r.to_data()
    args["authorisation"] = Authorisation(user=user,
                                          resource=r.signature())

    result = call_function("access", func, args)

    print(result)
