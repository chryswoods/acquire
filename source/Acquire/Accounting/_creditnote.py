
from ._debitnote import DebitNote as _DebitNote
from ._decimal import create_decimal as _create_decimal

__all__ = ["CreditNote"]


class CreditNote:
    """This class holds all of the information about a completed credit. This
       is combined with a debit note of equal value to form a transaction
       record
    """
    def __init__(self, debit_note=None, account=None, receipt=None,
                 refund=None, bucket=None):
        """Create the corresponding credit note for the passed debit_note. This
           will credit value from the note to the passed account. The credit
           will use the same UID as the credit, and the same timestamp. This
           will then be paired with the debit note to form a TransactionRecord
           that can be written to the ledger
        """
        self._account_uid = None

        nargs = (receipt is not None) + (refund is not None)

        if nargs > 1:
            raise ValueError("You can create a CreditNote with a receipt "
                             "or a refund - not both!")

        if receipt is not None:
            self._create_from_receipt(debit_note, receipt, account, bucket)

        elif refund is not None:
            self._create_from_refund(debit_note, refund, account, bucket)

        elif (debit_note is not None) and (account is not None):
            self._create_from_debit_note(debit_note, account, bucket)

        else:
            self._debit_account_uid = None
            self._timestamp = None
            self._uid = None
            self._debit_note_uid = None
            self._value = _create_decimal(0)

    def __str__(self):
        if self.is_null():
            return "CreditNote::null"
        else:
            return "CreditNote:%s>>%s" % (self.value(), self.account_uid())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._uid == other._uid
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_null(self):
        """Return whether or not this note is null"""
        return self._uid is None

    def account_uid(self):
        """Return the UID of the account to which the value was credited"""
        if self.is_null():
            return None
        else:
            return self._account_uid

    def credit_account_uid(self):
        """Synonym for self.account_uid()"""
        return self.account_uid()

    def debit_account_uid(self):
        """Return the UID of the account from which the value was debited"""
        if self.is_null():
            return None
        else:
            return self._debit_account_uid

    def timestamp(self):
        """Return the timestamp for this credit note"""
        return self._timestamp

    def uid(self):
        """Return the UID of this credit note. This will not match the debit
           note UID - you need to use debit_note_uid() to get the UID of
           the debit note that matches this credit note
        """
        return self._uid

    def debit_note_uid(self):
        """Return the UID of the debit note that matches this credit note.
           While at the moment only a single credit note matches a debit note,
           it may be in the future that we divide a credit over several
           accounts (and thus several credit notes)
        """
        return self._debit_note_uid

    def value(self):
        """Return the value of this note. This may be less than the
           corresponding debit note if only part of the value of the
           debit note is transferred into the account
        """
        return self._value

    def is_provisional(self):
        """Return whether or not this credit note is provisional
           (i.e. the value will only be transferred on completion
           of work and provision of a receipt)
        """
        if self.is_null():
            return False
        else:
            return self._is_provisional

    def _create_from_refund(self, debit_note, refund, account, bucket):
        """Internal function used to create the credit note from
           the passed refund. This will actually transfer value from the
           debit note to the credited account (which was the original
           debited account)
        """
        if not isinstance(debit_note, _DebitNote):
            raise TypeError("You can only create a CreditNote "
                            "with a DebitNote")

        from ._refund import Refund as _Refund

        if not isinstance(refund, _Refund):
            raise TypeError("You can only refund a Refund object: %s"
                            % str(refund.__class__))

        from ._transactionrecord import TransactionRecord as _TransactionRecord
        from ._transactionrecord import TransactionState as _TransactionState
        from ._account import Account as _Account

        # get the transaction behind this refund and ensure it is in the
        # refunding state...
        transaction = _TransactionRecord.load_test_and_set(
                        refund.transaction_uid(),
                        _TransactionState.REFUNDING,
                        _TransactionState.REFUNDING, bucket=bucket)

        # ensure that the receipt matches the transaction...
        transaction.assert_matching_refund(refund)

        if account is None:
            account = _Account(transaction.debit_account_uid(), bucket)
        elif account.uid() != refund.debit_account_uid():
            raise ValueError("The accounts do not match when refunding "
                             "the receipt: %s versus %s" %
                             (account.uid(), refund.debit_account_uid()))

        (uid, timestamp) = account._credit_refund(debit_note, refund, bucket)

        self._account_uid = account.uid()
        self._debit_account_uid = debit_note.account_uid()
        self._timestamp = timestamp
        self._uid = uid
        self._debit_note_uid = debit_note.uid()
        self._value = debit_note.value()
        self._is_provisional = debit_note.is_provisional()

        # finally(!) move the transaction into the refunded state
        _TransactionRecord.load_test_and_set(
                            refund.transaction_uid(),
                            _TransactionState.REFUNDING,
                            _TransactionState.REFUNDED, bucket=bucket)

    def _create_from_receipt(self, debit_note, receipt, account, bucket):
        """Internal function used to create the credit note from
           the passed receipt. This will actually transfer value from the
           debit note to the credited account
        """
        if not isinstance(debit_note, _DebitNote):
            raise TypeError("You can only create a CreditNote "
                            "with a DebitNote")

        from ._receipt import Receipt as _Receipt

        if not isinstance(receipt, _Receipt):
            raise TypeError("You can only receipt a Receipt object: %s"
                            % str(receipt.__class__))

        from ._transactionrecord import TransactionRecord as _TransactionRecord
        from ._transactionrecord import TransactionState as _TransactionState
        from ._account import Account as _Account

        # get the transaction behind this receipt and ensure it is in the
        # receipting state...
        transaction = _TransactionRecord.load_test_and_set(
                        receipt.transaction_uid(),
                        _TransactionState.RECEIPTING,
                        _TransactionState.RECEIPTING, bucket=bucket)

        # ensure that the receipt matches the transaction...
        transaction.assert_matching_receipt(receipt)

        if account is None:
            account = _Account(transaction.credit_account_uid(), bucket)
        elif account.uid() != receipt.credit_account_uid():
            raise ValueError("The accounts do not match when crediting "
                             "the receipt: %s versus %s" %
                             (account.uid(), receipt.credit_account_uid()))

        (uid, timestamp) = account._credit_receipt(debit_note, receipt, bucket)

        self._account_uid = account.uid()
        self._debit_account_uid = debit_note.account_uid()
        self._timestamp = timestamp
        self._uid = uid
        self._debit_note_uid = debit_note.uid()
        self._value = debit_note.value()
        self._is_provisional = debit_note.is_provisional()

        # finally(!) move the transaction into the receipted state
        _TransactionRecord.load_test_and_set(
                            receipt.transaction_uid(),
                            _TransactionState.RECEIPTING,
                            _TransactionState.RECEIPTED, bucket=bucket)

    def _create_from_debit_note(self, debit_note, account, bucket):
        """Internal function used to create the credit note that matches
           the passed debit note. This will actually transfer value from
           the debit note to the passed account
        """
        if not isinstance(debit_note, _DebitNote):
            raise TypeError("You can only create a CreditNote "
                            "with a DebitNote")

        from ._account import Account as _Account

        if not isinstance(account, _Account):
            raise TypeError("You can only create a CreditNote with an "
                            "Account")

        (uid, timestamp) = account._credit(debit_note, bucket=bucket)

        self._account_uid = account.uid()
        self._debit_account_uid = debit_note.account_uid()
        self._timestamp = timestamp
        self._uid = uid
        self._debit_note_uid = debit_note.uid()
        self._value = debit_note.value()
        self._is_provisional = debit_note.is_provisional()

    @staticmethod
    def from_data(data):
        """Construct and return a new CreditNote from the passed json-decoded
            dictionary
        """
        note = CreditNote()

        if (data and len(data) > 0):
            note._account_uid = data["account_uid"]
            note._debit_account_uid = data["debit_account_uid"]
            note._uid = data["uid"]
            note._debit_note_uid = data["debit_note_uid"]
            note._timestamp = data["timestamp"]
            note._value = _create_decimal(data["value"])
            note._is_provisional = data["is_provisional"]

        return note

    def to_data(self):
        """Return this credit note as a dictionary that can be
           encoded to json
        """
        data = {}

        if not self.is_null():
            data["account_uid"] = self._account_uid
            data["debit_account_uid"] = self._debit_account_uid
            data["uid"] = self._uid
            data["debit_note_uid"] = self._debit_note_uid
            data["timestamp"] = self._timestamp
            data["value"] = str(self._value)
            data["is_provisional"] = self._is_provisional

        return data
