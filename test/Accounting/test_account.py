
import pytest
import random
import datetime

from Acquire.Accounting import Account, Transaction, TransactionRecord, \
                               Accounts, Ledger, Receipt, Refund, \
                               create_decimal, Balance

from Acquire.Identity import Authorisation, ACLRule

from Acquire.Service import get_service_account_bucket, \
    push_is_running_service, pop_is_running_service, \
    is_running_service

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import get_datetime_now

account1_overdraft_limit = 1500000
account2_overdraft_limit = 2500000

account1_user = "account1@local"
account2_user = "account2@local"

testing_key = PrivateKey()


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
        push_is_running_service()
        bucket = get_service_account_bucket(str(d))
        while is_running_service():
            pop_is_running_service()

        return bucket


@pytest.fixture(scope="session")
def account1(bucket):
    push_is_running_service()
    accounts = Accounts(user_guid=account1_user)
    account = Account(name="Testing Account",
                      description="This is the test account",
                      group_name=accounts.name(),
                      bucket=bucket)
    uid = account.uid()
    assert(uid is not None)
    assert(account.balance() == Balance())

    account.set_overdraft_limit(account1_overdraft_limit)
    assert(account.get_overdraft_limit() == account1_overdraft_limit)
    pop_is_running_service()

    return account


@pytest.fixture(scope="session")
def account2(bucket):
    push_is_running_service()
    accounts = Accounts(user_guid=account2_user)
    account = Account(name="Testing Account",
                      description="This is a second testing account",
                      group_name=accounts.name(),
                      bucket=bucket)
    uid = account.uid()
    assert(uid is not None)
    assert(account.balance() == Balance())

    account.set_overdraft_limit(account2_overdraft_limit)
    assert(account.get_overdraft_limit() == account2_overdraft_limit)

    pop_is_running_service()

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

    push_is_running_service()

    try:
        account = Account(name, description, bucket=bucket)

        assert(account.name() == name)
        assert(account.description() == description)
        assert(not account.is_null())

        uid = account.uid()
        assert(uid is not None)

        account2 = Account(uid=uid, bucket=bucket)

        assert(account2.name() == name)
        assert(account2.description() == description)

        assert(account.balance() == Balance())
    except:
        pop_is_running_service()
        raise

    pop_is_running_service()


def test_transactions(random_transaction, bucket):

    (transaction, account1, account2) = random_transaction

    starting_balance1 = account1.balance()

    starting_balance2 = account2.balance()

    authorisation = Authorisation(resource=transaction.fingerprint(),
                                  testing_key=testing_key,
                                  testing_user_guid=account1.group_name())

    records = Ledger.perform(transaction=transaction,
                             debit_account=account1,
                             credit_account=account2,
                             authorisation=authorisation,
                             is_provisional=False,
                             bucket=bucket)

    assert(len(records) == 1)

    record = records[0]

    ending_balance1 = account1.balance()
    ending_balance2 = account2.balance()

    assert(ending_balance1 == starting_balance1 - transaction)
    assert(ending_balance2 == starting_balance2 + transaction)

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
    authorisation = Authorisation(resource=credit_note.fingerprint(),
                                  testing_key=testing_key,
                                  testing_user_guid=account2.group_name())

    refund = Refund(credit_note, authorisation)

    assert(not refund.is_null())
    assert(refund.authorisation() == authorisation)
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
    ending_balance2 = account2.balance()

    assert(ending_balance1.liability() == starting_balance1.liability())
    assert(ending_balance2.receivable() == starting_balance2.receivable())
    assert(starting_balance1.balance() == ending_balance1.balance())
    assert(starting_balance2.balance() == ending_balance2.balance())
    assert(starting_balance2.liability() == ending_balance2.liability())
    assert(starting_balance1.receivable() == ending_balance1.receivable())


def test_pending_transactions(random_transaction):
    (transaction, account1, account2) = random_transaction

    starting_balance1 = account1.balance()
    starting_balance2 = account2.balance()

    authorisation = Authorisation(resource=transaction.fingerprint(),
                                  testing_key=testing_key,
                                  testing_user_guid=account1.group_name())

    records = Ledger.perform(transactions=transaction,
                             debit_account=account1,
                             credit_account=account2,
                             authorisation=authorisation,
                             is_provisional=True)

    assert(len(records) == 1)
    record = records[0]

    ending_balance1 = account1.balance()
    ending_balance2 = account2.balance()

    assert(ending_balance1.liability() == starting_balance1.liability() +
           transaction.value())
    assert(ending_balance2.receivable() == starting_balance2.receivable() +
           transaction.value())
    assert(starting_balance1.balance() == ending_balance1.balance())
    assert(starting_balance2.balance() == ending_balance2.balance())
    assert(starting_balance2.liability() == ending_balance2.liability())
    assert(starting_balance1.receivable() == ending_balance1.receivable())

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
    authorisation = Authorisation(resource=credit_note.fingerprint(),
                                  testing_key=testing_key,
                                  testing_user_guid=account2.group_name())

    with pytest.raises(ValueError):
        receipt = Receipt(credit_note, authorisation,
                          create_decimal(random.random()) +
                          credit_note.value())

    if random.randint(0, 1):
        value = credit_note.value()
        receipt = Receipt(credit_note, authorisation)
    else:
        value = create_decimal(create_decimal(random.random()) *
                               credit_note.value())
        receipt = Receipt(credit_note, authorisation, value)

    assert(not receipt.is_null())
    assert(receipt.authorisation() == authorisation)
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
    ending_balance2 = account2.balance()

    assert(ending_balance1.liability() == starting_balance1.liability())
    assert(ending_balance2.receivable() == starting_balance2.receivable())
    assert(starting_balance1.balance() - value == ending_balance1.balance())
    assert(starting_balance2.balance() + value == ending_balance2.balance())
    assert(starting_balance2.liability() == ending_balance2.liability())
    assert(starting_balance1.receivable() == ending_balance1.receivable())
