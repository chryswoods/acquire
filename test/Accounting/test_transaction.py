
import pytest
import random

from Acquire.Accounting import Transaction, TransactionError, create_decimal


def test_transaction_is_null():
    t = Transaction()
    assert(t.is_null())


@pytest.fixture(params=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def random_transaction():
    value = create_decimal(1000.0 * random.random())
    description = "%s transaction" % value
    transaction = Transaction(value, description)

    assert(transaction.value() == value)
    assert(transaction.description() == description)

    return transaction


@pytest.fixture(params=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def random_large_value():
    return random.randrange(900000, 100000000)


def test_transaction_saving(random_transaction):
    t = random_transaction

    data = t.to_data()
    t2 = Transaction.from_data(data)

    assert(t.value() == t2.value())
    assert(t.description() == t2.description())
    assert(t == t2)


def test_descriptionless_fails(random_transaction):
    value = random_transaction.value()

    if value > 0:
        with pytest.raises(TransactionError):
            t = Transaction(value)
            assert(t.is_null())
    else:
        t = Transaction(value)


def test_negative_fails(random_transaction):
    value = -(random_transaction.value())

    if (value < 0):
        with pytest.raises(TransactionError):
            t = Transaction(value, "this is a negative transaction")
            assert(t.is_null())
    else:
        t = Transaction(value)


@pytest.mark.parametrize("value1, value2",
                         [(0.5, 0.8), (10, 20), (0, 0.000001)])
def test_comparison(value1, value2):
    t1 = Transaction(value1, "lower")
    t2 = Transaction(value2, "higher")

    assert(t1 < t2)
    assert(t2 > t1)
    assert(t1 < value2)
    assert(t2 > value1)
    assert(t1 >= value1)
    assert(t1 <= value1)
    assert(t2 >= value2)
    assert(t2 <= value2)
    assert(t1 == value1)
    assert(t2 == value2)
    assert(t1 == t1)
    assert(t2 == t2)
    assert(t1 != t2)
    assert(t2 != t1)
    assert(t1 != value2)
    assert(t2 != value1)


def test_split(random_large_value):
    value = random_large_value
    transactions = Transaction.split(value, "something")

    total = 0
    for transaction in transactions:
        total += transaction.value()

    total = Transaction.round(total)

    assert(total == Transaction.round(value))
