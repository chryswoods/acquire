
import pytest
import random
import datetime
from threading import Thread, RLock

from Acquire.Accounting import Account, Transaction, TransactionRecord, \
                               Ledger, Receipt, Refund, \
                               create_decimal

from Acquire.Identity import Authorisation

from Acquire.Service import login_to_service_account

try:
    from freezegun import freeze_time
    have_freezetime = True
except:
    have_freezetime = False

account1_overdraft_limit = 1500000
account2_overdraft_limit = 2500000

start_time = datetime.datetime.now() - datetime.timedelta(days=365)


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    try:
        return login_to_service_account()
    except:
        d = tmpdir_factory.mktemp("objstore")
        return login_to_service_account(str(d))


@pytest.fixture(scope="module")
def account1(bucket):
    if not have_freezetime:
        return None

    with freeze_time(start_time) as frozen_datetime:
        now = datetime.datetime.now()
        assert(frozen_datetime() == now)
        account = Account("Testing Account", "This is the test account")

        uid = account.uid()
        assert(uid is not None)
        assert(account.balance() == 0)
        assert(account.liability() == 0)

        account.set_overdraft_limit(account1_overdraft_limit)
        assert(account.get_overdraft_limit() == account1_overdraft_limit)

    return account


@pytest.fixture(scope="module")
def account2(bucket):
    if not have_freezetime:
        return None

    with freeze_time(start_time) as frozen_datetime:
        now = datetime.datetime.now()
        assert(frozen_datetime() == now)
        account = Account("Testing Account", "This is the test account")

        uid = account.uid()
        assert(uid is not None)
        assert(account.balance() == 0)
        assert(account.liability() == 0)

        account.set_overdraft_limit(account2_overdraft_limit)
        assert(account.get_overdraft_limit() == account2_overdraft_limit)

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
    now = datetime.datetime.now()
    for i in range(0, 100):
        random_dates.append(start_time + random.random() * (now - start_time))

    # (which must be applied in time order!)
    random_dates.sort()

    records = []

    for (i, transaction_time) in enumerate(random_dates):
        with freeze_time(transaction_time) as frozen_datetime:
            now = datetime.datetime.now()
            assert(frozen_datetime() == now)

            is_provisional = random.randint(0, 5)

            transaction = Transaction(25*random.random(),
                                      "test transaction %d" % i)
            auth = Authorisation()

            if random.randint(0, 10):
                record = Ledger.perform(transaction, account1, account2,
                                        auth, is_provisional,
                                        bucket=bucket)

                if is_provisional:
                    liability1 += transaction.value()
                    receivable2 += transaction.value()
                else:
                    balance1 -= transaction.value()
                    balance2 += transaction.value()

                final_balance1 -= transaction.value()
                final_balance2 += transaction.value()
            else:
                record = Ledger.perform(transaction, account2, account1,
                                        auth, is_provisional,
                                        bucket=bucket)

                if is_provisional:
                    receivable1 += transaction.value()
                    liability2 += transaction.value()
                else:
                    balance1 += transaction.value()
                    balance2 -= transaction.value()

                final_balance1 += transaction.value()
                final_balance2 -= transaction.value()

            if is_provisional:
                records.append(record)

            assert(record.timestamp() == now.timestamp())

    assert(account1.balance() == balance1)
    assert(account2.balance() == balance2)
    assert(account1.liability() == liability1)
    assert(account1.receivable() == receivable1)
    assert(account2.liability() == liability2)
    assert(account2.receivable() == receivable2)

    for record in records:
        Ledger.receipt(Receipt(record.credit_note(), Authorisation()),
                       bucket=bucket)

    assert(account1.balance() == final_balance1)
    assert(account2.balance() == final_balance2)

    assert(account1.liability() == zero)
    assert(account1.receivable() == zero)
    assert(account2.liability() == zero)
    assert(account2.receivable() == zero)


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
        auth = Authorisation()

        # need to work with thread-local copies of the accounts
        my_account1 = Account(uid=account1.uid())
        my_account2 = Account(uid=account2.uid())

        for i in range(0, 5):
            transaction = Transaction(value=create_decimal(random.random()),
                                      description="Transaction %d" % i)

            if random.randint(0, 1):
                Ledger.perform(transaction, my_account1, my_account2, auth)
                delta1 -= transaction.value()
                delta2 += transaction.value()
            else:
                Ledger.perform(transaction, my_account2, my_account1, auth)
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
