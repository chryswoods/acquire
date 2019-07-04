
from Acquire.Access import RunRequest
from Acquire.Identity import Authorisation
from Acquire.Client import Account, deposit, Cheque, Service, \
                           Drive, StorageCreds


def _testdata():
    """Return the path to the directory containing test data"""
    import os
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

    # Upload a directory that will contain all of the input
    creds = StorageCreds(user=user, service_url="storage")
    drive = Drive(name="sim", creds=creds, autocreate=True)

    location = drive.upload(_testdata())

    print(drive.list_files(dir="example_sim/input"))

    print(location)

    assert(False)

    # create a request for the calculation described in 'run.yaml' and
    # authorise it using the authenticated user (who may be different to the
    # user who pays for the job - hence the need for a different
    # authorisation for the request and for the cheque)
    runfile = "%s/run.yaml" % _testdata()
    r = RunRequest(runfile=runfile)

    # now write a cheque which will provide authorisation to spend money from
    # this account to pay for this request. This will be written to the access
    # service to give it the authority to create a transation in the account.
    # This cheque authorises only a single transaction, performable only
    # by the service whose canonical URL is supplied, and the access service
    # should check that the requested resource signature matches that
    # authorised by the cheque
    cheque = Cheque.write(account=account,
                          recipient_url="access",
                          resource=r.fingerprint(),
                          max_spend=50.0)

    func = "run_calculation"
    args = {}
    args["request"] = r.to_data()
    args["authorisation"] = Authorisation(user=user,
                                          resource=r.fingerprint()).to_data()
    args["cheque"] = cheque.to_data()

    access_service = Service("access")
    result = access_service.call_function(func, args)
