
from Acquire.Service import login_to_service_account \
                    as _login_to_service_account

from Acquire.Identity import Authorisation as _Authorisation

from ._transaction import Transaction as _Transaction

from ._errors import LedgerError

__all__ = ["DebitNote"]


class DebitNote:
    """This class holds all of the information about a completed debit. This
       is combined with credit note of equal value to form a transaction record
    """
    def __init__(self, transaction=None, account=None, authorisation=None,
                 is_provisional=False, receipt=None, refund=None, bucket=None):
        """Create a debit note for the passed transaction will debit value
           from the passed account. The note will create a unique ID (uid)
           for the debit, plus the timestamp of the time that value was drawn
           from the debited account. This debit note will be paired with a
           corresponding credit note from the account that received the value
           from the transaction so that a balanced TransactionRecord can be
           written to the ledger
        """
        self._transaction = None

        nargs = (transaction is not None) + (refund is not None) + \
                (receipt is not None)

        if nargs > 1:
            raise ValueError("You can only choose to create a debit note "
                             "from a transaction, receipt or refund!")

        if refund is not None:
            self._create_from_refund(refund, account, bucket)
        elif receipt is not None:
            self._create_from_receipt(receipt, account, bucket)
        elif (transaction is not None):
            if account is None:
                raise ValueError("You need to supply the account from "
                                 "which the transaction will be taken")

            self._create_from_transaction(transaction, account, authorisation,
                                          is_provisional, bucket)

    def __str__(self):
        if self.is_null():
            return "DebitNote::null"
        else:
            return "DebitNote:%s>>%s" % (self.account_uid(), self.value())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._uid == other._uid
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_null(self):
        """Return whether or not this is a null note"""
        return self._transaction is None

    def uid(self):
        """Return the UID for this note. This has the format
           dd:mm:yyyy/unique_string
        """
        if self.is_null():
            return None
        else:
            return self._uid

    def timestamp(self):
        """Return the timestamp for when value was debited from the account"""
        if self.is_null():
            return None
        else:
            return self._timestamp

    def account_uid(self):
        """Return the UID of the account that was debited"""
        if self.is_null():
            return None
        else:
            return self._account_uid

    def transaction(self):
        """Return the transaction related to this debit note"""
        if self.is_null():
            return None
        else:
            return self._transaction

    def value(self):
        """Return the value of this note"""
        if self.is_null():
            return 0
        else:
            return self.transaction().value()

    def authorisation(self):
        """Return the authorisation that was used successfully to withdraw
           value from the debited account
        """
        if self.is_null():
            return None
        else:
            return self._authorisation

    def is_provisional(self):
        """Return whether or not the debit was provisional. Provisional debits
           are listed as liabilities
        """
        if self.is_null():
            return False
        else:
            return self._is_provisional

    def _create_from_refund(self, refund, account, bucket):
        """Function used to construct a debit note by extracting
           the value specified in the passed refund from the specified
           account. This is authorised using the authorisation held in
           the refund. Note that the refund must match
           up with a prior existing provisional transaction, and this
           must not have already been refunded. This will
           actually take value out of the passed account, with that
           value residing in this debit note until it is credited to
           another account
        """
        from ._refund import Refund as _Refund

        if not isinstance(refund, _Refund):
            raise TypeError("You can only create a DebitNote with a "
                            "Refund")

        if refund.is_null():
            return

        if bucket is None:
            bucket = _login_to_service_account()

        from ._transactionrecord import TransactionRecord as _TransactionRecord
        from ._transactionrecord import TransactionState as _TransactionState
        from ._account import Account as _Account

        # get the transaction behind this refund and move it into
        # the "refunding" state
        transaction = _TransactionRecord.load_test_and_set(
                        refund.transaction_uid(),
                        _TransactionState.DIRECT,
                        _TransactionState.REFUNDING, bucket=bucket)

        try:
            # ensure that the receipt matches the transaction...
            transaction.assert_matching_refund(refund)

            if account is None:
                account = _Account(transaction.credit_account_uid(), bucket)
            elif account.uid() != refund.credit_account_uid():
                raise ValueError("The accounts do not match when debiting "
                                 "the refund: %s versus %s" %
                                 (account.uid(), refund.credit_account_uid()))

            # now move the refund from the credit account back to the
            # debit note
            (uid, timestamp) = account._debit_refund(refund, bucket)

            self._transaction = refund.transaction()
            self._account_uid = refund.credit_account_uid()
            self._authorisation = refund.authorisation()
            self._is_provisional = False

            self._timestamp = float(timestamp)
            self._uid = str(uid)
        except:
            # move the transaction back to its original state...
            _TransactionRecord.load_test_and_set(
                        refund.transaction_uid(),
                        _TransactionState.REFUNDING,
                        _TransactionState.DIRECT)
            raise

    def _create_from_receipt(self, receipt, account, bucket):
        """Function used to construct a debit note by extracting
           the value specified in the passed receipt from the specified
           account. This is authorised using the authorisation held in
           the receipt, based on the original authorisation given in the
           provisional transaction. Note that the receipt must match
           up with a prior existing provisional transaction, and this
           must not have already been receipted or refunded. This will
           actually take value out of the passed account, with that
           value residing in this debit note until it is credited to
           another account
        """
        from ._receipt import Receipt as _Receipt

        if not isinstance(receipt, _Receipt):
            raise TypeError("You can only create a DebitNote with a "
                            "Receipt")

        if receipt.is_null():
            return

        if bucket is None:
            bucket = _login_to_service_account()

        from ._transactionrecord import TransactionRecord as _TransactionRecord
        from ._transactionrecord import TransactionState as _TransactionState
        from ._account import Account as _Account

        # get the transaction behind this receipt and move it into
        # the "receipting" state
        transaction = _TransactionRecord.load_test_and_set(
                        receipt.transaction_uid(),
                        _TransactionState.PROVISIONAL,
                        _TransactionState.RECEIPTING, bucket=bucket)

        try:
            # ensure that the receipt matches the transaction...
            transaction.assert_matching_receipt(receipt)

            if account is None:
                account = _Account(transaction.debit_account_uid(), bucket)
            elif account.uid() != receipt.debit_account_uid():
                raise ValueError("The accounts do not match when debiting "
                                 "the receipt: %s versus %s" %
                                 (account.uid(), receipt.debit_account_uid()))

            # now move value from liability to debit, and then into this
            # debit note
            (uid, timestamp) = account._debit_receipt(receipt, bucket)

            self._transaction = receipt.transaction()
            self._account_uid = receipt.debit_account_uid()
            self._authorisation = receipt.authorisation()
            self._is_provisional = False

            self._timestamp = float(timestamp)
            self._uid = str(uid)
        except:
            # move the transaction back to its original state...
            _TransactionRecord.load_test_and_set(
                        receipt.transaction_uid(),
                        _TransactionState.RECEIPTING,
                        _TransactionState.PROVISIONAL)
            raise

    def _create_from_transaction(self, transaction, account, authorisation,
                                 is_provisional, bucket):
        """Function used to construct a debit note by extracting the
           specified transaction value from the passed account. This
           is authorised using the passed authorisation, and can be
           a provisional debit if 'is_provisional' is true. This will
           actually take value out of the passed account, with that
           value residing in this debit note until it is credited
           to another account
        """
        if not isinstance(transaction, _Transaction):
            raise TypeError("You can only create a DebitNote with a "
                            "Transaction")

        from ._account import Account as _Account

        if not isinstance(account, _Account):
            raise TypeError("You can only create a DebitNote with a valid "
                            "Account")

        if authorisation is not None:
            from Acquire.Identity import Authorisation as _Authorisation

            if not isinstance(authorisation, _Authorisation):
                raise TypeError("Authorisation must be of type Authorisation")

        self._transaction = transaction
        self._account_uid = account.uid()
        self._authorisation = authorisation
        self._is_provisional = is_provisional

        (uid, timestamp) = account._debit(transaction, authorisation,
                                          is_provisional, bucket=bucket)

        self._timestamp = float(timestamp)
        self._uid = str(uid)

    def to_data(self):
        """Return this DebitNote as a dictionary that can be encoded as json"""
        data = {}

        if not self.is_null():
            data["transaction"] = self._transaction.to_data()
            data["account_uid"] = self._account_uid
            data["authorisation"] = self._authorisation.to_data()
            data["is_provisional"] = self._is_provisional
            data["timestamp"] = self._timestamp
            data["uid"] = self._uid

        return data

    @staticmethod
    def from_data(data):
        """Return a DebitNote that has been extracted from the passed
           json-decoded dictionary
        """
        d = DebitNote()

        if (data and len(data) > 0):
            d._transaction = _Transaction.from_data(data["transaction"])
            d._account_uid = data["account_uid"]
            d._authorisation = _Authorisation.from_data(data["authorisation"])
            d._is_provisional = data["is_provisional"]
            d._timestamp = data["timestamp"]
            d._uid = data["uid"]

        return d
