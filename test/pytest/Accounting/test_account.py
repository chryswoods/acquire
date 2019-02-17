
import pytest
import random
import datetime

from Acquire.Accounting import Account, Transaction, TransactionRecord, \
                               Ledger, Receipt, Refund, \
                               create_decimal

from Acquire.Identity import Authorisation

from Acquire.Service import get_service_account_bucket

from Acquire.ObjectStore import get_datetime_now

account1_overdraft_limit = 1500000
account2_overdraft_limit = 2500000


def assert_packable(obj):
    data = obj.to_data()
    new_obj = obj.__class__.from_data(data)
    assert(obj == new_obj)


@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    try:
        return get_service_account_bucket()
    except:
        d = tmpdir_factory.mktemp("objstore")
        return get_service_account_bucket(str(d))


@pytest.fixture(scope="session")
def account1(bucket):
    account = Account("Testing Account", "This is the test account",
                      bucket=bucket)
    uid = account.uid()
    assert(uid is not None)
    assert(account.balance() == 0)
    assert(account.liability() == 0)

    account.set_overdraft_limit(account1_overdraft_limit)
    assert(account.get_overdraft_limit() == account1_overdraft_limit)

    return account


@pytest.fixture(scope="session")
def account2(bucket):
    account = Account("Testing Account", "This is a second testing account",
                      bucket=bucket)
    uid = account.uid()
    assert(uid is not None)
    assert(account.balance() == 0)
    assert(account.liability() == 0)

    account.set_overdraft_limit(account2_overdraft_limit)
    assert(account.get_overdraft_limit() == account2_overdraft_limit)

    return account


@pytest.fixture(params=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def random_transaction(account1, account2):
    value = create_decimal(1000.0 * random.random())
    description = "%s transaction" % value
    transaction = Transaction(value, description)

    assert(transaction.value() == value)
    assert(transaction.description() == description)

    assert(account1.get_overdraft_limit() == account1_overdraft_limit)
    assert(account2.get_overdraft_limit() == account2_overdraft_limit)

    if random.randint(0, 1):
        return (transaction, account1, account2)
    else:
        return (transaction, account2, account1)


def test_account(bucket):
    name = "test account"
    description = "This is a test account"

    account = Account(name, description, bucket=bucket)

    assert(account.name() == name)
    assert(account.description() == description)
    assert(not account.is_null())

    uid = account.uid()
    assert(uid is not None)

    account2 = Account(uid=uid, bucket=bucket)

    assert(account2.name() == name)
    assert(account2.description() == description)

    assert(account.balance() == 0)


def test_transactions(random_transaction, bucket):
    (transaction, account1, account2) = random_transaction

    starting_balance1 = account1.balance()
    starting_liability1 = account1.liability()
    starting_receivable1 = account1.receivable()

    starting_balance2 = account2.balance()
    starting_liability2 = account2.liability()
    starting_receivable2 = account2.receivable()

    records = Ledger.perform(transaction, account1, account2,
                             Authorisation(), is_provisional=False,
                             bucket=bucket)

    assert(len(records) == 1)

    record = records[0]

    ending_balance1 = account1.balance()
    ending_liability1 = account1.liability()
    ending_receivable1 = account1.receivable()

    ending_balance2 = account2.balance()
    ending_liability2 = account2.liability()
    ending_receivable2 = account2.receivable()

    assert(ending_balance1 == starting_balance1 - transaction.value())
    assert(ending_balance2 == starting_balance2 + transaction.value())

    assert(ending_liability1 == starting_liability1)
    assert(starting_liability2 == ending_liability2)
    assert(starting_receivable1 == ending_receivable1)
    assert(starting_receivable2 == ending_receivable2)

    assert(record.debit_account_uid() == account1.uid())
    assert(record.credit_account_uid() == account2.uid())

    debit_note = record.debit_note()
    credit_note = record.credit_note()

    assert(debit_note.account_uid() == account1.uid())
    assert(credit_note.account_uid() == account2.uid())

    assert(not debit_note.is_provisional())
    assert(not credit_note.is_provisional())

    assert(debit_note.value() == transaction.value())
    assert(credit_note.value() == transaction.value())

    now = get_datetime_now()

    assert(debit_note.datetime() < now)
    assert(credit_note.datetime() < now)
    assert(debit_note.datetime() <= credit_note.datetime())

    assert_packable(debit_note)
    assert_packable(credit_note)

    # now test refunding this transaction
    # now receipt a random amount of the transaction
    auth = Authorisation()

    refund = Refund(credit_note, auth)

    assert(not refund.is_null())
    assert(refund.authorisation() == auth)
    assert(refund.value() == transaction.value())
    assert(refund.credit_note() == credit_note)
    assert_packable(refund)

    rrecords = Ledger.refund(refund)

    assert(len(rrecords) == 1)
    rrecord = rrecords[0]

    assert(not rrecord.is_null())
    assert_packable(rrecord)

    assert(not rrecord.is_provisional())
    assert(rrecord.is_direct())
    assert(rrecord.get_refund_info() == refund)
    assert(rrecord.is_refund())
    assert(rrecord.original_transaction() == transaction)

    # the original transaction record has now been updated to
    # say that it has been receipted...
    assert(record.is_direct())
    record.reload()
    assert(record.is_refunded())

    assert(rrecord.original_transaction_record() == record)

    ending_balance1 = account1.balance()
    ending_liability1 = account1.liability()
    ending_receivable1 = account1.receivable()

    ending_balance2 = account2.balance()
    ending_liability2 = account2.liability()
    ending_receivable2 = account2.receivable()

    assert(ending_liability1 == starting_liability1)
    assert(ending_receivable2 == starting_receivable2)
    assert(starting_balance1 == ending_balance1)
    assert(starting_balance2 == ending_balance2)
    assert(starting_liability2 == ending_liability2)
    assert(starting_receivable1 == ending_receivable1)


def test_pending_transactions(random_transaction):
    (transaction, account1, account2) = random_transaction

    starting_balance1 = account1.balance()
    starting_liability1 = account1.liability()
    starting_receivable1 = account1.receivable()

    starting_balance2 = account2.balance()
    starting_liability2 = account2.liability()
    starting_receivable2 = account2.receivable()

    records = Ledger.perform(transaction, account1, account2,
                             Authorisation(), is_provisional=True)

    assert(len(records) == 1)
    record = records[0]

    ending_balance1 = account1.balance()
    ending_liability1 = account1.liability()
    ending_receivable1 = account1.receivable()

    ending_balance2 = account2.balance()
    ending_liability2 = account2.liability()
    ending_receivable2 = account2.receivable()

    assert(ending_liability1 == starting_liability1 + transaction.value())
    assert(ending_receivable2 == starting_receivable2 + transaction.value())
    assert(starting_balance1 == ending_balance1)
    assert(starting_balance2 == ending_balance2)
    assert(starting_liability2 == ending_liability2)
    assert(starting_receivable1 == ending_receivable1)

    assert(record.debit_account_uid() == account1.uid())
    assert(record.credit_account_uid() == account2.uid())

    debit_note = record.debit_note()
    credit_note = record.credit_note()

    assert(not debit_note.is_null())
    assert(not credit_note.is_null())

    assert(debit_note.account_uid() == account1.uid())
    assert(credit_note.account_uid() == account2.uid())

    assert(debit_note.is_provisional())
    assert(credit_note.is_provisional())

    assert(debit_note.value() == transaction.value())
    assert(credit_note.value() == transaction.value())

    now = get_datetime_now()

    assert(debit_note.datetime() < now)
    assert(credit_note.datetime() < now)
    assert(debit_note.datetime() <= credit_note.datetime())

    assert_packable(debit_note)
    assert_packable(credit_note)

    # now receipt a random amount of the transaction
    auth = Authorisation()

    with pytest.raises(ValueError):
        receipt = Receipt(credit_note, auth,
                          create_decimal(random.random()) +
                          credit_note.value())

    if random.randint(0, 1):
        value = credit_note.value()
        receipt = Receipt(credit_note, auth)
    else:
        value = create_decimal(create_decimal(random.random()) *
                               credit_note.value())
        receipt = Receipt(credit_note, auth, value)

    assert(not receipt.is_null())
    assert(receipt.authorisation() == auth)
    assert(receipt.receipted_value() == value)
    assert(receipt.credit_note() == credit_note)
    assert_packable(receipt)

    rrecords = Ledger.receipt(receipt)

    assert(len(rrecords) == 1)
    rrecord = rrecords[0]

    assert(not rrecord.is_null())
    assert_packable(rrecord)

    assert(not rrecord.is_provisional())
    assert(rrecord.is_direct())
    assert(rrecord.get_receipt_info() == receipt)
    assert(rrecord.is_receipt())
    assert(rrecord.original_transaction() == transaction)

    # the original transaction record has now been updated to
    # say that it has been receipted...
    assert(record.is_provisional())
    record.reload()
    assert(record.is_receipted())

    assert(rrecord.original_transaction_record() == record)

    ending_balance1 = account1.balance()
    ending_liability1 = account1.liability()
    ending_receivable1 = account1.receivable()

    ending_balance2 = account2.balance()
    ending_liability2 = account2.liability()
    ending_receivable2 = account2.receivable()

    assert(ending_liability1 == starting_liability1)
    assert(ending_receivable2 == starting_receivable2)
    assert(starting_balance1 - value == ending_balance1)
    assert(starting_balance2 + value == ending_balance2)
    assert(starting_liability2 == ending_liability2)
    assert(starting_receivable1 == ending_receivable1)
