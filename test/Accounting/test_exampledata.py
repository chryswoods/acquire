
import pytest
import os
import distutils
from distutils import dir_util

from Acquire.Accounting import Account, Accounts

from Acquire.Service import push_is_running_service, get_service_account_bucket


@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    try:
        return get_service_account_bucket()
    except:
        d = tmpdir_factory.mktemp("objstore")
        push_is_running_service()
        return get_service_account_bucket(str(d))


def test_example_data(bucket):
    example_dir = "%s/example_data" % os.path.split(__file__)[0]

    assert(os.path.exists("%s/accounting" % example_dir))

    # copy the accounting data into the object store
    distutils.dir_util.copy_tree(example_dir, bucket)

    user1_accounts = Accounts("e2e31e35-025c-4a4c-8a7b-65da94e722d6")
    user2_accounts = Accounts("e5e03b59-bc04-4a7f-9ebd-9c32dbc795f6")

    accounts = []

    for account in user1_accounts.list_accounts():
        accounts.append(user1_accounts.get_account(account))

    for account in user2_accounts.list_accounts():
        accounts.append(user2_accounts.get_account(account))

    # make sure that the ledger is balanced
    balance_sum = 0
    some_nonzero = False

    for account in accounts:
        balance = account.balance()

        if balance != 0:
            some_nonzero = True

        balance_sum += balance

    assert(some_nonzero)
    assert(balance_sum == 0)
