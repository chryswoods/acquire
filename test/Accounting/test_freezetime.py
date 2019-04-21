
import pytest
import random
import datetime
from threading import Thread, RLock

from Acquire.Accounting import Account, Transaction, TransactionRecord, \
                               Ledger, Receipt, Refund, \
                               create_decimal, Balance, Accounts

from Acquire.Identity import Authorisation

from Acquire.ObjectStore import get_datetime_now

from Acquire.Crypto import PrivateKey

from Acquire.Service import get_service_account_bucket, is_running_service, \
    push_is_running_service, pop_is_running_service

try:
    from freezegun import freeze_time
    have_freezetime = True
except:
    have_freezetime = False

account1_user = "account11@local"
account2_user = "account12@local"

account1_overdraft_limit = 1500000
account2_overdraft_limit = 2500000

testing_key = PrivateKey()

start_time = get_datetime_now() - datetime.timedelta(days=365)


@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    try:
        return get_service_account_bucket()
    except:
        d = tmpdir_factory.mktemp("objstore")
        push_is_running_service()
        bucket = get_service_account_bucket(str(d))
        while is_running_service():
            pop_is_running_service()
        return bucket


@pytest.fixture(scope="session")
def account1(bucket):
    if not have_freezetime:
        return None

    with freeze_time(start_time) as _frozen_datetime:
        now = get_datetime_now()
        assert(start_time == now)
        push_is_running_service()
        accounts = Accounts(user_guid=account1_user)
        account = Account(name="Testing Account",
                          description="This is the test account",
                          group_name=accounts.name())
        uid = account.uid()
        assert(uid is not None)
        assert(account.balance() == Balance())

        account.set_overdraft_limit(account1_overdraft_limit)
        assert(account.get_overdraft_limit() == account1_overdraft_limit)
        pop_is_running_service()

    return account


@pytest.fixture(scope="session")
def account2(bucket):
    if not have_freezetime:
        return None

    with freeze_time(start_time) as _frozen_datetime:
        now = get_datetime_now()
        assert(start_time == now)
        push_is_running_service()
        accounts = Accounts(user_guid=account2_user)
        account = Account(name="Testing Account",
                          description="This is a second testing account",
                          group_name=accounts.name())
        uid = account.uid()
        assert(uid is not None)
        assert(account.balance() == Balance())

        account.set_overdraft_limit(account2_overdraft_limit)
        assert(account.get_overdraft_limit() == account2_overdraft_limit)

        pop_is_running_service()

    return account


def test_temporal_transactions(account1, account2, bucket):
    if not have_freezetime:
        return

    zero = create_decimal(0)

    balance1 = zero
    balance2 = zero
    final_balance1 = zero
    final_balance2 = zero
    liability1 = zero
    liability2 = zero
    receivable1 = zero
    receivable2 = zero

    # generate some random times for the transactions
    random_dates = []
    now = get_datetime_now()
    for i in range(0, 25):
        random_dates.append(start_time + random.random() * (now - start_time))

    # (which must be applied in time order!)
    random_dates.sort()

    provisionals = []

    for (i, transaction_time) in enumerate(random_dates):
        with freeze_time(transaction_time) as _frozen_datetime:
            now = get_datetime_now()
            assert(transaction_time == now)

            is_provisional = False  # (random.randint(0, 3) <= 2)

            # check search for transaction is not O(n^2) lookup scanning
            # through the keys...

            transaction = Transaction(25*random.random(),
                                      "test transaction %d" % i)

            print(transaction)

            if random.randint(0, 1):
                debit_account = account1
                credit_account = account2

                if is_provisional:
                    liability1 += transaction.value()
                    receivable2 += transaction.value()
                else:
                    balance1 -= transaction.value()
                    balance2 += transaction.value()

                final_balance1 -= transaction.value()
                final_balance2 += transaction.value()
            else:
                debit_account = account2
                credit_account = account1

                if is_provisional:
                    receivable1 += transaction.value()
                    liability2 += transaction.value()
                else:
                    balance1 += transaction.value()
                    balance2 -= transaction.value()

                final_balance1 += transaction.value()
                final_balance2 -= transaction.value()

            auth = Authorisation(
                        resource=transaction.fingerprint(),
                        testing_key=testing_key,
                        testing_user_guid=debit_account.group_name())

            records = Ledger.perform(transaction=transaction,
                                     debit_account=debit_account,
                                     credit_account=credit_account,
                                     authorisation=auth,
                                     is_provisional=is_provisional,
                                     bucket=bucket)

            for record in records:
                assert(record.datetime() == now)

            if is_provisional:
                for record in records:
                    provisionals.append((credit_account, record))
            elif True:  #(random.randint(0, 3) <= 2):
                # receipt pending transactions
                balance1 = Balance(balance=balance1, liability=liability1,
                                   receivable=receivable1)

                balance2 = Balance(balance=balance2, liability=liability2,
                                   receivable=receivable2)

                assert(account1.balance() == balance1)
                assert(account2.balance() == balance2)

                for (credit_account, record) in provisionals:
                    auth = Authorisation(
                            resource=record.credit_note().fingerprint(),
                            testing_key=testing_key,
                            testing_user_guid=credit_account.group_name())

                    Ledger.receipt(Receipt(record.credit_note(), auth),
                                   bucket=bucket)

                assert(account1.balance() == Balance(balance=final_balance1))
                assert(account2.balance() == Balance(balance=final_balance2))

                provisionals = []
                balance1 = final_balance1
                balance2 = final_balance2
                liability1 = zero
                liability2 = zero
                receivable1 = zero
                receivable2 = zero

    balance1 = Balance(balance=balance1, liability=liability1,
                       receivable=receivable1)

    balance2 = Balance(balance=balance2, liability=liability2,
                       receivable=receivable2)

    assert(account1.balance() == balance1)
    assert(account2.balance() == balance2)

    for (credit_account, record) in provisionals:
        auth = Authorisation(resource=record.credit_note().fingerprint(),
                             testing_key=testing_key,
                             testing_user_guid=credit_account.group_name())

        Ledger.receipt(Receipt(record.credit_note(), auth),
                       bucket=bucket)

    assert(account1.balance() == Balance(balance=final_balance1))
    assert(account2.balance() == Balance(balance=final_balance2))


def test_parallel_transaction(account1, account2, bucket):
    if not have_freezetime:
        return

    zero = create_decimal(0)

    # test lots of transactions all happening in parallel
    total1 = zero
    total2 = zero

    start1 = account1.balance()
    start2 = account2.balance()

    rlock = RLock()

    def perform_transaction(key, result):
        delta1 = zero
        delta2 = zero

        # need to work with thread-local copies of the accounts
        my_account1 = Account(uid=account1.uid())
        my_account2 = Account(uid=account2.uid())

        for i in range(0, 10):
            transaction = Transaction(value=create_decimal(random.random()),
                                      description="Transaction %d" % i)

            if random.randint(0, 1):
                auth = Authorisation(
                        resource=transaction.fingerprint(),
                        testing_key=testing_key,
                        testing_user_guid=my_account1.group_name())

                Ledger.perform(transaction=transaction,
                               debit_account=my_account1,
                               credit_account=my_account2,
                               authorisation=auth)
                delta1 -= transaction.value()
                delta2 += transaction.value()
            else:
                auth = Authorisation(
                        resource=transaction.fingerprint(),
                        testing_key=testing_key,
                        testing_user_guid=my_account2.group_name())

                Ledger.perform(transaction=transaction,
                               debit_account=my_account2,
                               credit_account=my_account1,
                               authorisation=auth)
                delta1 += transaction.value()
                delta2 -= transaction.value()

        with rlock:
            result[key] = (delta1, delta2)

    threads = []

    result = {}

    for i in range(0, 5):
        t = Thread(target=perform_transaction, args=[i, result])
        t.start()
        threads.append(t)

    total1 = zero
    total2 = zero

    for i, thread in enumerate(threads):
        thread.join()
        total1 += result[i][0]
        total2 += result[i][1]

    assert(account1.balance() == start1 + total1)
    assert(account2.balance() == start2 + total2)
