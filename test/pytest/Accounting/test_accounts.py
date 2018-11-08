
import pytest

from Acquire.Accounting import Accounts

from Acquire.Service import login_to_service_account


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    try:
        return login_to_service_account()
    except:
        d = tmpdir_factory.mktemp("objstore")
        return login_to_service_account(str(d))


def test_accounts(bucket):
    for group in [None, "chris", "ƒ˚®ø©∆∂µ"]:
        accounts = Accounts(group=group)

        account_names = ["new account", "chris's checking account",
                         "å∫ç∂´® account"]

        created_accounts = {}

        for name in account_names:
            account = accounts.create_account(
                        name,
                        description="Account: %s" % name,
                        bucket=bucket)

            assert(name == account.name())

            created_accounts[name] = account

        names = accounts.list_accounts()

        for name in account_names:
            assert(name in names)

        for name in account_names:
            account = accounts.get_account(name, bucket=bucket)
            assert(name == account.name())

            assert(account == created_accounts[name])
