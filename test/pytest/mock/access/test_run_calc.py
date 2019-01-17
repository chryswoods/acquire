
import pytest
import os

from Acquire.Access import RunRequest
from Acquire.Identity import Authorisation
from Acquire.Service import call_function, get_remote_service_info
from Acquire.Client import Account, deposit
from Acquire.Crypto import PrivateKey


def _testdata():
    """Return the path to the directory containing test data"""
    return os.path.dirname(os.path.abspath(__file__)) + \
        os.path.sep + "example_sim"


def test_run_calc(aaai_services, authenticated_user):
    user = authenticated_user
    assert(user.is_logged_in())

    # ensure that the main account has money
    deposit(user, 100.0, "Adding money to the account",
            accounting_url="accounting")

    # get a handle to the financial account used to pay for the job
    account = Account(user=user, account_name="deposits",
                      accounting_url="accounting")

    assert(account.balance() >= 100.0)

    # now write a cheque which will provide authorisation to spend money from
    # this account. This will be written to the access service to
    # give it the authority to create a transation in the account.
    # This cheque authorises only a single transaction, performable only
    # by the service whose canonical URL is supplied
    cheque = account.write_cheque(canonical_url="access",
                                  max_spend=50.0)

    # create a request for the calculation described in 'run.yaml' and
    # authorise it using the authenticated user (who may be different to the
    # user who pays for the job - hence the need for a different
    # authorisation for the request and for the cheque)
    runfile = "%s/run.yaml" % _testdata()
    r = RunRequest(runfile=runfile)

    func = "run_calculation"
    args = {}
    args["request"] = r.to_data()
    args["authorisation"] = Authorisation(user=user,
                                          resource=r.signature())
    args["cheque"] = cheque

    access_service = get_remote_service_info("access")
    result = access_service.call_function(func, args)

    assert(result["status"] == 0)
