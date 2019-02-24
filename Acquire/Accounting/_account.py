
import uuid as _uuid
from copy import copy as _copy
import datetime as _datetime
import time as _time
import re as _re

__all__ = ["Account"]


def _account_root():
    return "accounting/accounts"


def _get_key_from_date(start, datetime):
    """Return a key encoding the passed date, starting the key with 'start'"""
    from Acquire.ObjectStore import datetime_to_datetime \
        as _datetime_to_datetime
    datetime = _datetime_to_datetime(datetime)
    return "%s/%s" % (start, datetime.date().isoformat())


def _get_date_from_key(key):
    """Return the date that is encoded in the passed key"""
    m = _re.search(r"(\d\d\d\d)-(\d\d)-(\d\d)", key)

    if m:
        from Acquire.ObjectStore import date_and_time_to_datetime \
            as _date_and_time_to_datetime

        return _date_and_time_to_datetime(
                    _datetime.date(year=int(m.groups()[0]),
                                   month=int(m.groups()[1]),
                                   day=int(m.groups()[2])))
    else:
        from Acquire.Accounting import AccountError
        raise AccountError("Could not find a date in the key '%s'" % key)


def _get_datetime_from_key(key):
    """Return the datetime that is encoded in the passed key"""
    m = _re.search(r"(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)\.(\d+)",
                   key)

    if m:
        from Acquire.ObjectStore import date_and_time_to_datetime \
            as _datetime_to_datetime

        return _datetime_to_datetime(
                    _datetime.datetime(year=int(m.groups()[0]),
                                       month=int(m.groups()[1]),
                                       day=int(m.groups()[2]),
                                       hour=int(m.groups()[3]),
                                       minute=int(m.groups()[4]),
                                       second=int(m.groups()[5]),
                                       microsecond=int(m.groups()[6])))
    else:
        from Acquire.Accounting import AccountError
        raise AccountError("Could not find a datetime in the key '%s'" % key)


def _sum_transactions(keys):
    """Internal function that sums all of the transactions identified
        by the passed keys. This returns a tuple of
        (balance, liability, receivable, spent_today)
    """
    from Acquire.Accounting import create_decimal as _create_decimal
    from Acquire.Accounting import TransactionInfo as _TransactionInfo

    balance = _create_decimal(0)
    liability = _create_decimal(0)
    receivable = _create_decimal(0)
    spent_today = _create_decimal(0)

    for key in keys:
        if isinstance(key, _TransactionInfo):
            v = key
        else:
            v = _TransactionInfo(key)

        if v.is_credit():
            balance += v.value()
        elif v.is_debit():
            balance -= v.value()
            spent_today += v.value()
        elif v.is_liability():
            liability += v.value()
            spent_today += v.value()
        elif v.is_accounts_receivable():
            receivable += v.value()
        elif v.is_received_receipt():
            balance -= v.receipted_value()
            liability -= v.value()
        elif v.is_sent_receipt():
            balance += v.receipted_value()
            receivable -= v.value()
        elif v.is_received_refund():
            balance += v.value()
        elif v.is_sent_refund():
            balance -= v.value()

    return (balance, liability, receivable, spent_today)


class Account:
    """This class represents a single account in the ledger. It has a balance,
       and a record of the set of transactions that have been applied.

       The account really holds two accounts: the liability account and
       actual capital account. We combine both together into a single
       account to ensure that updates occur atomically

       All data for this account is stored in the object store
    """
    def __init__(self, name=None, description=None, uid=None, bucket=None):
        """Construct the account. If 'uid' is specified, then load the account
           from the object store (so 'name' and 'description' should be "None")
        """
        if uid is not None:
            self._uid = str(uid)
            self._name = None
            self._description = None
            self._last_update_datetime = None
            self._load_account(bucket)

            if name:
                if name != self.name():
                    from Acquire.Accounting import AccountError
                    raise AccountError(
                        "This account name '%s' does not match what you "
                        "expect! '%s'" % (self.name(), name))

            if description:
                if description != self.description():
                    from Acquire.Accounting import AccountError
                    raise AccountError(
                        "This account description '%s' does not match what "
                        "you expect! '%s'" % (self.description(), description))

        elif name is not None:
            self._uid = None
            self._create_account(name, description)
        else:
            self._uid = None
            self._last_update_datetime = None

    def __str__(self):
        if self._uid is None:
            return "Account::null"
        else:
            return "Account(%s|%s|%s)" % (self._name, self._description,
                                          self._uid)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._uid == other._uid
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def _create_account(self, name, description):
        """Create the account from scratch"""
        if name is None or description is None:
            from Acquire.Accounting import AccountError
            raise AccountError(
                "You must pass both a name and description to create a new "
                "account")

        if self._uid is not None:
            from Acquire.Accounting import AccountError
            raise AccountError("You cannot create an account twice!")

        from Acquire.Accounting import create_decimal as _create_decimal
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        self._uid = str(_uuid.uuid4())
        self._name = str(name)
        self._description = str(description)
        self._overdraft_limit = _create_decimal(0)
        self._maximum_daily_limit = 0
        self._last_update_datetime = None

        # initialise the account with a balance of zero
        bucket = _get_service_account_bucket()
        self._record_daily_balance(0, 0, 0, bucket=bucket)

        # make sure that this is saved to the object store
        self._save_account(bucket)

    def _get_balance_key(self, datetime=None):
        """Return the balance key for the passed time. This is the key
           into the object store of the object that holds the starting
           balance for the account on the day of the passed datetime.
           If datetime is None, then today's key is returned
        """
        if self.is_null():
            return None

        if datetime is None:
            from Acquire.ObjectStore import get_datetime_now \
                as _get_datetime_now
            datetime = _get_datetime_now()
        else:
            from Acquire.ObjectStore import datetime_to_datetime \
                as _datetime_to_datetime
            datetime = _datetime_to_datetime(datetime)

        return _get_key_from_date("%s/balance" % self._key(),
                                  datetime)

    def _record_daily_balance(self, balance, liability, receivable,
                              datetime=None, bucket=None):
        """Record the starting balance for the day containing 'datetime'
           as 'balance' with the starting outstanding liabilities at
           'liability' and starting outstanding accounts receivable at
           'receivable' If 'datetime' is none, then the balance
           for today is set.
        """
        if self.is_null():
            return

        if datetime is None:
            from Acquire.ObjectStore import get_datetime_now \
                as _get_datetime_now
            datetime = _get_datetime_now()
        else:
            from Acquire.ObjectStore import datetime_to_datetime \
                as _datetime_to_datetime
            datetime = _datetime_to_datetime(datetime)

        from Acquire.Accounting import create_decimal as _create_decimal

        balance = _create_decimal(balance)
        liability = _create_decimal(liability)
        receivable = _create_decimal(receivable)

        balance_key = self._get_balance_key(datetime)

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        data = {"balance": str(balance),
                "liability": str(liability),
                "receivable": str(receivable)}

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        _ObjectStore.set_object_from_json(bucket, balance_key, data)

    def _reconcile_daily_accounts(self, bucket=None):
        """Internal function used to reconcile the daily accounts.
           This ensures that every line item transaction is summed up
           so that the starting balance for each day is recorded into
           the object store
        """
        if self.is_null():
            return

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        # work back from today to the first day of the account to calculate
        # all of the daily balances... We need to record every day of the
        # account to support quick lookups
        from Acquire.ObjectStore import get_datetime_now \
            as _get_datetime_now
        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        today = _get_datetime_now().toordinal()
        day = today
        last_data = None
        num_missing_days = 0

        while last_data is None:
            daytime = _datetime.datetime.fromordinal(day)
            key = self._get_balance_key(daytime)
            last_data = _ObjectStore.get_object_from_json(bucket, key)

            if last_data is None:
                day -= 1
                num_missing_days += 1

                if num_missing_days > 100:
                    # we need another strategy to find the last balance
                    break

        if last_data is None:
            # find the latest day by reading the keys in the object
            # store directly
            root = "%s/balance/" % self._key()
            keys = _ObjectStore.get_all_object_names(
                        bucket, root)

            if keys is None or len(keys) == 0:
                from Acquire.Accounting import AccountError
                raise AccountError(
                    "There is no daily balance recorded for "
                    "the account with UID %s" % self.uid())

            # the encoding of the keys is such that, when sorted, the
            # last key must be the latest balance
            keys.sort()

            last_data = _ObjectStore.get_object_from_json(
                            bucket, keys[-1])
            day = _get_date_from_key(keys[-1]).toordinal()

            if last_data is None:
                raise AccountError("How can there be no data for key %s?" %
                                   keys[-1])

        # what was the balance on the last day?
        from Acquire.Accounting import create_decimal as _create_decimal
        result = (_create_decimal(last_data["balance"]),
                  _create_decimal(last_data["liability"]),
                  _create_decimal(last_data["receivable"]))

        # ok, now we go from the last day until today and sum up the
        # line items from each day to create the daily balances
        # (not including today, as we only want the balance at the beginning
        #  of today)
        for d in range(day+1, today+1):
            day_time = _datetime.datetime.fromordinal(d)
            transaction_keys = self._get_transaction_keys_between(
                            _datetime.datetime.fromordinal(d-1),
                            day_time)

            total = _sum_transactions(transaction_keys)

            result = (result[0]+total[0], result[1]+total[1],
                      result[2]+total[2])

            balance_key = self._get_balance_key(day_time)

            data = {}
            data["balance"] = str(result[0])
            data["liability"] = str(result[1])
            data["receivable"] = str(result[2])

            _ObjectStore.set_object_from_json(bucket, balance_key, data)

    def _get_daily_balance(self, bucket=None, datetime=None):
        """Get the daily starting balance for the passed datetime. This
           returns a tuple of
           (balance, liability, receivable).

           where 'balance' is the current real balance of the account,
           neglecting any outstanding liabilities or accounts receivable,
           where 'liability' is the current total liabilities,
           where 'receivable' is the current total accounts receivable, and

           If datetime is None then todays daily balance is returned. The
           daily balance is the balance at the start of the day. The
           actual balance at a particular time will be this starting
           balance plus/minus all of the transactions between the start
           of that day and the specified datetime
        """
        if self.is_null():
            return

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        if datetime is None:
            from Acquire.ObjectStore import get_datetime_now \
                as _get_datetime_now
            datetime = _get_datetime_now()
        else:
            from Acquire.ObjectStore import datetime_to_datetime \
                as _datetime_to_datetime
            datetime = _datetime_to_datetime(datetime)

        balance_key = self._get_balance_key(datetime)

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        data = _ObjectStore.get_object_from_json(bucket, balance_key)

        if data is None:
            # there is no balance for this day. This means that we haven'y
            # yet calculated that day's balance. Do the accounting necessary
            # to construct that day's starting balance
            self._reconcile_daily_accounts(bucket)

            data = _ObjectStore.get_object_from_json(bucket, balance_key)

            if data is None:
                from Acquire.Accounting import AccountError
                raise AccountError("The daily balance for account at date %s "
                                   "is not available" % str(datetime))

        from Acquire.Accounting import create_decimal as _create_decimal

        return (_create_decimal(data["balance"]),
                _create_decimal(data["liability"]),
                _create_decimal(data["receivable"]))

    def _get_balance(self, bucket=None, datetime=None):
        """Get the balance of the account for the passed datetime. This
           returns a tuple of

           (balance, liability, receivable)

           where 'balance' is the current real balance of the account,
           neglecting any outstanding liabilities or accounts receivable,
           where 'liability' is the current total liabilities,
           where 'receivable' is the current total accounts receivable

           If datetime is None then the balance "now" is returned
        """
        if datetime is None:
            return self._get_current_balance(bucket)

        raise NotImplementedError("NOT IMPLEMENTED!")

    def _get_transaction_keys_between(self, start_datetime, end_datetime,
                                      bucket=None):
        """Return all of the object store keys for transactions in this
           account beteen 'start_datetime' and 'end_datetime' (inclusive, e.g.
           start_datetime <= transaction <= end_datetime). This will return an
           empty list if there were no transactions in this time
        """
        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        # convert both times to UTC
        from Acquire.ObjectStore import datetime_to_datetime \
            as _datetime_to_datetime
        start_datetime = _datetime_to_datetime(start_datetime)
        end_datetime = _datetime_to_datetime(end_datetime)

        # get the day for each time
        start_day = start_datetime.toordinal()
        end_day = end_datetime.toordinal()

        if end_datetime.time() == _datetime.time():
            # this ends on midnight of the first day - do not
            # include this last day as nothing will match
            end_day -= 1

        keys = []

        from Acquire.ObjectStore import string_to_datetime \
            as _string_to_datetime
        from Acquire.ObjectStore import date_to_string as _date_to_string
        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        for day in range(start_day, end_day+1):
            day_date = _datetime.datetime.fromordinal(day)
            day_string = _date_to_string(day_date)

            prefix = "%s/%s" % (self._key(), day_string)
            len_prefix = len(prefix)

            day_keys = _ObjectStore.get_all_object_names(bucket, prefix)

            for day_key in day_keys:
                # the key is Ttime/rest_of_key
                day_key = day_key[len_prefix:]
                time = day_key.split("/")[0]

                datetime = _string_to_datetime("%s%s" % (day_string, time))

                if datetime >= start_datetime and datetime < end_datetime:
                    keys.append("%s/%s" % (prefix, day_key))

        return keys

    def _recalculate_current_balance(self, bucket, now):
        """Internal function that implements _get_current_balance
           by recalculating the total from today from scratch
        """
        # where were we at the start of today?
        from Acquire.ObjectStore import datetime_to_datetime \
            as _datetime_to_datetime
        now = _datetime_to_datetime(now)

        (balance, liability, receivable) = self._get_daily_balance(bucket,
                                                                   now)

        # now sum up all of the transactions from today
        from Acquire.ObjectStore import date_and_time_to_datetime \
            as _date_and_time_to_datetime
        start_today = _date_and_time_to_datetime(now.date())

        transaction_keys = self._get_transaction_keys_between(start_today, now)

        total = _sum_transactions(transaction_keys)

        result = (balance+total[0], liability+total[1], receivable+total[2],
                  total[3])

        self._last_update_datetime = now
        self._last_update = result

        return result

    def last_update_datetime(self):
        """Return the last time the balance was updated, as a datetime
           object
        """
        if self._last_update_datetime is None:
            # this is the earliest datetime possible
            from Acquire.ObjectStore import date_and_time_to_datetime \
                as _date_and_time_to_datetime
            return _date_and_time_to_datetime(_datetime.date.fromordinal(1))
        else:
            return self._last_update_datetime

    def _update_current_balance(self, bucket, now):
        """Internal function that implements _get_current_balance
           by updating the balance etc. from transactions that have
           occurred since the last update
        """
        (balance, liability, receivable, spent_today) = self._last_update

        from Acquire.ObjectStore import datetime_to_datetime \
            as _datetime_to_datetime

        now = _datetime_to_datetime(now)

        # now sum up all of the transactions since the last update
        transaction_keys = self._get_transaction_keys_between(
                                            self.last_update_datetime(),
                                            now)

        total = _sum_transactions(transaction_keys)

        result = (balance+total[0], liability+total[1], receivable+total[2],
                  spent_today+total[3])

        self._last_update_datetime = now
        self._last_update = result

        return result

    def _get_current_balance(self, bucket=None):
        """Get the balance of the account now (the current balance). This
           returns a tuple of
           (balance, liability, receivable, spent_today).

           where 'balance' is the current real balance of the account,
           neglecting any outstanding liabilities or accounts receivable,
           where 'liability' is the current total liabilities,
           where 'receivable' is the current total accounts receivable, and
           where 'spent_today' is how much has been spent today (from midnight
           until now)
        """
        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import get_datetime_now \
            as _get_datetime_now

        now = _get_datetime_now()

        last_update_datetime = self.last_update_datetime()

        if last_update_datetime.date() != now.date():
            # we are on a new day since the last update, so recalculate
            # the balance from scratch
            return self._recalculate_current_balance(bucket, now)
        else:
            # we have calculated the total before today. Get the transactions
            # since the last update and use these to update the daily spend
            # etc.
            return self._update_current_balance(bucket, now)

    def is_null(self):
        """Return whether or not this is a null account"""
        return self._uid is None

    def name(self):
        """Return the name of this account"""
        if self.is_null():
            return None

        return self._name

    def description(self):
        """Return the description of this account"""
        if self.is_null():
            return None

        return self._description

    def uid(self):
        """Return the UID for this account."""
        return self._uid

    def _key(self):
        """Return the key for this account in the object store"""
        if self.is_null():
            return None

        return "%s/%s" % (_account_root(), self.uid())

    def _load_account(self, bucket=None):
        """Load the current state of the account from the object store"""
        if self.is_null():
            return

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        data = _ObjectStore.get_object_from_json(bucket, self._key())
        self.__dict__ = _copy(Account.from_data(data).__dict__)

    def _save_account(self, bucket=None):
        """Save this account back to the object store"""
        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        _ObjectStore.set_object_from_json(bucket, self._key(), self.to_data())

    def to_data(self):
        """Return a dictionary that can be encoded to json from this object"""
        data = {}

        if not self.is_null():
            data["uid"] = self._uid
            data["name"] = self._name
            data["description"] = self._description
            data["overdraft_limit"] = str(self._overdraft_limit)
            data["maximum_daily_limit"] = str(self._maximum_daily_limit)

        return data

    @staticmethod
    def from_data(data):
        """Construct and return an Account from the passed dictionary that has
           been decoded from json
        """
        account = Account()

        if (data and len(data) > 0):
            from Acquire.Accounting import create_decimal as _create_decimal

            account._uid = data["uid"]
            account._name = data["name"]
            account._description = data["description"]
            account._overdraft_limit = _create_decimal(data["overdraft_limit"])
            account._maximum_daily_limit = _create_decimal(
                                                data["maximum_daily_limit"])

        return account

    def assert_valid_authorisation(self, authorisation):
        """Assert that the passed authorisation is valid for this
           account
        """
        from Acquire.Identity import Authorisation as _Authorisation
        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The passed authorisation must be an "
                            "Authorisation")

    def _get_safe_now(self):
        """This function returns the current time. It avoids dangerous
           times (when the system may be updating) by sleeping through
           those times
        """
        from Acquire.ObjectStore import get_datetime_now \
            as _get_datetime_now
        now = _get_datetime_now()

        # don't allow any transactions in the last 30 seconds of the day, as we
        # will sum up the day balance at midnight, and don't want to risk any
        # late transactions from messing up the accounting
        while now.hour == 23 and now.minute == 59 and now.second >= 30:
            _time.sleep(5)
            now = _get_datetime_now()

        return now

    def _delete_note(self, note, bucket=None):
        """Internal function called to delete the passed note from the
           record. This is unsafe and should only be called from
           DebitNote.return_value or CreditNote.return_value (which
           themselves are only called from Ledger)
        """
        if note is None:
            return

        from Acquire.Accounting import DebitNote as _DebitNote
        from Acquire.Accounting import CreditNote as _CreditNote

        if isinstance(note, _DebitNote) or isinstance(note, _CreditNote):
            item_key = "%s/%s" % (self._key(), note.uid())

            if bucket is None:
                from Acquire.Service import get_service_account_bucket \
                    as _get_service_account_bucket
                bucket = _get_service_account_bucket()

            # remove the note
            from Acquire.ObjectStore import ObjectStore as _ObjectStore
            from Acquire.ObjectStore import get_datetime_now \
                as _get_datetime_now

            try:
                _ObjectStore.delete_object(bucket, item_key)
            except:
                pass

            # now remove all day-balances from the day before this note
            # to today. Hopefully this will prevent any ledger errors...
            day0 = note.datetime().toordinal() - 1
            day1 = _get_datetime_now().toordinal()

            for day in range(day0, day1+1):
                balance_key = self._get_balance_key(
                                    _datetime.datetime.fromordinal(day))

                try:
                    _ObjectStore.delete_object(bucket, balance_key)
                except:
                    pass

    def _credit_refund(self, debit_note, refund, bucket=None):
        """Credit the value of the passed 'refund' to this account. The
           refund must be for a previous completed debit, hence the
           original debitted value is returned to the account.
        """
        from Acquire.Accounting import Refund as _Refund
        from Acquire.Accounting import DebitNote as _DebitNote

        if not isinstance(refund, _Refund):
            raise TypeError("The passed refund must be a Refund")

        if not isinstance(debit_note, _DebitNote):
            raise TypeError("The passed debit note must be a DebitNote")

        if refund.is_null():
            return

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        if refund.value() != debit_note.value():
            raise ValueError("The refunded value does not match the value "
                             "of the debit note: %s versus %s" %
                             (refund.value(), debit_note.value()))

        from Acquire.Accounting import TransactionInfo as _TransactionInfo
        from Acquire.Accounting import TransactionCode as _TransactionCode

        encoded_value = _TransactionInfo.encode(
                                        _TransactionCode.RECEIVED_REFUND,
                                        refund.value())

        # create a UID and datetime for this credit and record
        # it in the account
        now = self._get_safe_now()

        # and to create a key to find this credit later. The key is made
        # up from the iso format of the datetime of the credit
        # and a random string
        from Acquire.ObjectStore import datetime_to_string \
            as _datetime_to_string
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Accounting import LineItem as _LineItem

        day_key = _datetime_to_string(now)
        uid = "%s/%s" % (day_key, str(_uuid.uuid4())[0:8])

        item_key = "%s/%s/%s" % (self._key(), uid, encoded_value)
        l = _LineItem(debit_note.uid(), refund.authorisation())

        _ObjectStore.set_object_from_json(bucket, item_key, l.to_data())

        return (uid, now)

    def _debit_refund(self, refund, bucket=None):
        """Debit the value of the passed 'refund' from this account. The
           refund must be for a previous completed credit. There is a risk
           that this value has been spent, so this is one of the only
           functions that allows a balance to drop below an overdraft or
           other limit (as the refund should always succeed).
        """
        from Acquire.Accounting import Refund as _Refund

        if not isinstance(refund, _Refund):
            raise TypeError("The passed refund must be a Refund")

        if refund.is_null():
            return

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        from Acquire.Accounting import TransactionInfo as _TransactionInfo
        from Acquire.Accounting import TransactionCode as _TransactionCode

        encoded_value = _TransactionInfo.encode(_TransactionCode.SENT_REFUND,
                                                refund.value())

        # create a UID and datetime for this debit and record
        # it in the account
        now = self._get_safe_now()

        # and to create a key to find this debit later. The key is made
        # up from the date and  of the debit and a random string
        from Acquire.ObjectStore import datetime_to_string \
            as _datetime_to_string
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Accounting import LineItem as _LineItem

        day_key = _datetime_to_string(now)
        uid = "%s/%s" % (day_key, str(_uuid.uuid4())[0:8])

        item_key = "%s/%s/%s" % (self._key(), uid, encoded_value)
        l = _LineItem(uid, refund.authorisation())

        _ObjectStore.set_object_from_json(bucket, item_key, l.to_data())

        return (uid, now)

    def _credit_receipt(self, debit_note, receipt, bucket=None):
        """Credit the value of the passed 'receipt' to this account. The
           receipt must be for a previous provisional credit, hence the
           money is awaiting transfer from accounts receivable.
        """
        from Acquire.Accounting import Receipt as _Receipt
        from Acquire.Accounting import DebitNote as _DebitNote

        if not isinstance(receipt, _Receipt):
            raise TypeError("The passed receipt must be a Receipt")

        if not isinstance(debit_note, _DebitNote):
            raise TypeError("The passed debit note must be a DebitNote")

        if receipt.is_null():
            return

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        if receipt.receipted_value() != debit_note.value():
            raise ValueError("The receipted value does not match the value "
                             "of the debit note: %s versus %s" %
                             (receipt.receipted_value(), debit_note.value()))

        from Acquire.Accounting import TransactionInfo as _TransactionInfo
        from Acquire.Accounting import TransactionCode as _TransactionCode

        encoded_value = _TransactionInfo.encode(
                                    _TransactionCode.SENT_RECEIPT,
                                    receipt.value(), receipt.receipted_value())

        # create a UID and datetime for this credit and record
        # it in the account
        now = self._get_safe_now()

        # and to create a key to find this credit later. The key is made
        # up from the isoformat datetime of the credit and a random string
        from Acquire.ObjectStore import datetime_to_string \
            as _datetime_to_string
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Accounting import LineItem as _LineItem

        day_key = _datetime_to_string(now)
        uid = "%s/%s" % (day_key, str(_uuid.uuid4())[0:8])

        item_key = "%s/%s/%s" % (self._key(), uid, encoded_value)
        l = _LineItem(debit_note.uid(), receipt.authorisation())

        _ObjectStore.set_object_from_json(bucket, item_key, l.to_data())

        return (uid, now)

    def _debit_receipt(self, receipt, bucket=None):
        """Debit the value of the passed 'receipt' from this account. The
           receipt must be for a previous provisional debit, hence
           the money should be available.
        """
        from Acquire.Accounting import Receipt as _Receipt

        if not isinstance(receipt, _Receipt):
            raise TypeError("The passed receipt must be a Receipt")

        if receipt.is_null():
            return

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        from Acquire.Accounting import TransactionInfo as _TransactionInfo
        from Acquire.Accounting import TransactionCode as _TransactionCode

        encoded_value = _TransactionInfo.encode(
                                    _TransactionCode.RECEIVED_RECEIPT,
                                    receipt.value(), receipt.receipted_value())

        # create a UID and datetime for this debit and record
        # it in the account
        now = self._get_safe_now()

        # and to create a key to find this debit later. The key is made
        # up from the isoformat datetime of the debit and a random string
        from Acquire.ObjectStore import datetime_to_string \
            as _datetime_to_string
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Accounting import LineItem as _LineItem

        day_key = _datetime_to_string(now)
        uid = "%s/%s" % (day_key, str(_uuid.uuid4())[0:8])

        item_key = "%s/%s/%s" % (self._key(), uid, encoded_value)
        l = _LineItem(uid, receipt.authorisation())

        _ObjectStore.set_object_from_json(bucket, item_key, l.to_data())

        return (uid, now)

    def _credit(self, debit_note, bucket=None):
        """Credit the value in 'debit_note' to this account. If the debit_note
           shows that the payment is provisional then this will be recorded
           as accounts receivable. This will record the credit with the
           same UID as the debit identified in the debit_note, so that
           we can reconcile all credits against matching debits.
        """
        from Acquire.Accounting import DebitNote as _DebitNote

        if not isinstance(debit_note, _DebitNote):
            raise TypeError("The passed debit note must be a DebitNote")

        if debit_note.value() <= 0:
            return

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        from Acquire.Accounting import TransactionInfo as _TransactionInfo
        from Acquire.Accounting import TransactionCode as _TransactionCode

        if debit_note.is_provisional():
            encoded_value = _TransactionInfo.encode(
                                _TransactionCode.ACCOUNT_RECEIVABLE,
                                debit_note.value())
        else:
            encoded_value = _TransactionInfo.encode(
                                _TransactionCode.CREDIT,
                                debit_note.value())

        # create a UID and datetime for this credit and record
        # it in the account
        now = self._get_safe_now()

        # and to create a key to find this credit later. The key is made
        # up from the isoformat datetime of the credit and a random string
        from Acquire.ObjectStore import datetime_to_string \
            as _datetime_to_string
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Accounting import LineItem as _LineItem

        day_key = _datetime_to_string(now)
        uid = "%s/%s" % (day_key, str(_uuid.uuid4())[0:8])

        item_key = "%s/%s/%s" % (self._key(), uid, encoded_value)

        # the line item records the UID of the debit note, so we can
        # find this debit note in the system and, from this, get the
        # original transaction in the transaction record
        l = _LineItem(debit_note.uid(), debit_note.authorisation())

        _ObjectStore.set_object_from_json(bucket, item_key, l.to_data())

        return (uid, now)

    def _debit(self, transaction, authorisation,
               is_provisional, receipt_by, bucket=None):
        """Debit the value of the passed transaction from this account based
           on the authorisation contained
           in 'authorisation'. This will create a unique ID (UID) for
           this debit and will return this together with the datetime of the
           debit. If this transaction 'is_provisional' then it will be
           recorded as a liability, which must be receipted before
           'receipt_by'. If 'receipt_by' is None, then this will
           automatically be 1 week in the future

           The UID will encode both the date of the debit and provide a random
           ID that together can be used to identify the transaction associated
           with this debit in the future.

           This will raise an exception if the debit cannot be completed, e.g.
           if the authorisation is invalid, if the debit exceeds a limit or
           there are insufficient funds in the account

           Note that this function is private as it should only be called
           by the DebitNote class
        """
        if self.is_null() or transaction.value() <= 0:
            return None

        from Acquire.Accounting import Transaction as _Transaction

        if not isinstance(transaction, _Transaction):
            raise TypeError("The passed transaction must be a Transaction!")

        self.assert_valid_authorisation(authorisation)

        if bucket is None:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            bucket = _get_service_account_bucket()

        if self.available_balance(bucket) < transaction.value():
            from Acquire.Accounting import InsufficientFundsError
            raise InsufficientFundsError(
                "You cannot debit '%s' from account %s as there "
                "are insufficient funds in this account." %
                (transaction, str(self)))

        # create a UID and datetime for this debit and record
        # it in the account
        now = self._get_safe_now()

        from Acquire.ObjectStore import datetime_to_string \
            as _datetime_to_string
        from Acquire.ObjectStore import datetime_to_datetime \
            as _datetime_to_datetime
        from Acquire.ObjectStore import get_datetime_future \
            as _get_datetime_future
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Accounting import LineItem as _LineItem

        from Acquire.Accounting import TransactionInfo as _TransactionInfo
        from Acquire.Accounting import TransactionCode as _TransactionCode

        if is_provisional:
            if receipt_by is None:
                receipt_by = _get_datetime_future(days=7)
            else:
                receipt_by = _datetime_to_datetime(receipt_by)

            delta = (receipt_by - now).total_seconds()
            if delta < 3600:
                from Acquire.Accounting import AccountError
                raise AccountError(
                    "You cannot request a receipt to be provided less "
                    "than 1 hour into the future! %s versus %s is only "
                    "%s second(s) in the future!" %
                    (_datetime_to_string(receipt_by),
                     _datetime_to_string(now), delta))
        else:
            receipt_by = None

        # and to create a key to find this debit later. The key is made
        # up from the isoformat datetime of the debit and a random string
        day_key = _datetime_to_string(now)
        uid = "%s/%s" % (day_key, str(_uuid.uuid4())[0:8])

        # the key in the object store is a combination of the key for this
        # account plus the uid for the debit plus the actual debit value.
        # We record the debit value in the key so that we can accumulate
        # the balance from just the key names
        if is_provisional:
            encoded_value = _TransactionInfo.encode(
                                _TransactionCode.CURRENT_LIABILITY,
                                transaction.value())
        else:
            encoded_value = _TransactionInfo.encode(
                                _TransactionCode.DEBIT,
                                transaction.value())

        item_key = "%s/%s/%s" % (self._key(), uid, encoded_value)

        # create a line_item for this debit and save it to the object store
        line_item = _LineItem(uid, authorisation)

        _ObjectStore.set_object_from_json(bucket, item_key,
                                          line_item.to_data())

        if self.is_beyond_overdraft_limit(bucket):
            # This transaction has helped push the account beyond the
            # overdraft limit. Delete the transaction and raise
            # an InsufficientFundsError

            _ObjectStore.delete_object(bucket, item_key)
            raise InsufficientFundsError(
                "You cannot debit '%s' from account %s as there "
                "are insufficient funds in this account." %
                (transaction, str(self)))

        return (uid, now, receipt_by)

    def available_balance(self, bucket=None):
        """Return the available balance of this account. This is the amount
           of value that can be spent (e.g. includes overdraft and fixed daily
           spend limits, and except any outstanding liabilities)
        """
        result = self._get_current_balance(bucket)

        balance = result[0]
        liabilities = result[1]
        spent_today = result[2]

        available = balance - liabilities + self.get_overdraft_limit()

        if self._maximum_daily_limit:
            return min(available, self._maximum_daily_limit - spent_today)
        else:
            return available

    def balance(self, bucket=None):
        """Return the current balance of this account"""
        result = self._get_current_balance(bucket)
        return result[0]

    def liability(self, bucket=None):
        """Return the current total liability of this account"""
        result = self._get_current_balance(bucket)
        return result[1]

    def receivable(self, bucket=None):
        """Return the current total accounts receivable of this account"""
        result = self._get_current_balance(bucket)
        return result[2]

    def spent_today(self, bucket=None):
        """Return the current amount spent today on this account"""
        result = self._get_current_balance(bucket)
        return result[3]

    def balance_status(self, bucket=None):
        """Return the overall balance status as a dictionary
           with keys 'balance', 'liability', 'receivable' and
           'spent_today'
        """
        result = self._get_current_balance(bucket)
        d = {}
        d["balance"] = result[0]
        d["liability"] = result[1]
        d["receivable"] = result[2]
        d["spent_today"] = result[3]
        return d

    def get_overdraft_limit(self):
        """Return the overdraft limit of this account"""
        if self.is_null():
            return 0

        return self._overdraft_limit

    def set_overdraft_limit(self, limit, bucket=None):
        """Set the overdraft limit of this account to 'limit'"""
        if self.is_null():
            return

        from Acquire.Accounting import create_decimal as _create_decimal
        limit = _create_decimal(limit)
        if limit < 0:
            raise ValueError("You cannot set the overdraft limit to a "
                             "negative value! (%s)" % limit)

        old_limit = self._overdraft_limit

        if old_limit != limit:
            self._overdraft_limit = limit

            if self.is_beyond_overdraft_limit():
                # restore the old limit
                self._overdraft_limit = old_limit
                from Acquire.Accounting import AccountError
                raise AccountError("You cannot change the overdraft limit to "
                                   "%s as this is greater than the current "
                                   "balance!" % (limit))
            else:
                # save the new limit to the object store
                self._save_account(bucket)

    def is_beyond_overdraft_limit(self, bucket=None):
        """Return whether or not the current balance is beyond
           the overdraft limit
        """
        result = self._get_current_balance(bucket)

        return (result[0] - result[1]) < -(self.get_overdraft_limit())
