
from enum import Enum as _Enum

__all__ = ["TransactionInfo", "TransactionCode"]


class TransactionCode(_Enum):
    CREDIT = "CR"
    DEBIT = "DR"
    CURRENT_LIABILITY = "CL"
    ACCOUNT_RECEIVABLE = "AR"
    RECEIVED_RECEIPT = "RR"
    SENT_RECEIPT = "SR"
    RECEIVED_REFUND = "RF"
    SENT_REFUND = "SF"


class TransactionInfo:
    """This class is used to encode and extract the type of transaction
       and value to/from an object store key
    """
    def __init__(self, key):
        """Extract information from the passed object store key.
           This looks for the string in the key that matches
           '2 letters followed by a number'

           CL000100.005000
           DR000004.234100

           etc.

           For sent and received receipts there are two values;
           the receipted value and the original estimate. These
           have the standard format if the values are the same, e.g.

           RR000100.005000

           however, they have original value T receipted value if they are
           different, e.g.

           RR000100.005000T000090.000000
        """
        from Acquire.Accounting import create_decimal as _create_decimal

        parts = key.split("/")

        # start at the end...
        for i in range(-1, -len(parts), -1):
            part = parts[i]

            try:
                code = TransactionInfo._get_code(part[0:2])

                if code == TransactionCode.SENT_RECEIPT or \
                        code == TransactionCode.RECEIVED_RECEIPT:

                    values = part[2:].split("T")
                    try:
                        value = _create_decimal(values[0])
                        receipted_value = _create_decimal(values[1])
                        self._code = code
                        self._value = value
                        self._receipted_value = receipted_value
                        return
                    except:
                        pass

                value = _create_decimal(part[2:])

                self._code = code
                self._value = value
                self._receipted_value = value
                return
            except:
                pass

        raise ValueError("Cannot extract transaction info from '%s'"
                         % (key))

    def __str__(self):
        return "TransactionInfo(code==%s, value==%s)" % \
                    (self._code.value, self._value)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._code == other._code and \
                   self._value == other._value
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def _get_code(code):
        """Return the TransactionCode matching 'code'"""
        return TransactionCode(code)

    @staticmethod
    def encode(code, value, receipted_value=None):
        """Encode the passed code and value into a simple string that can
           be used as part of an object store key. If 'receipted_value' is
           passed, then encode the receipted value of the provisional
           transaction too
        """
        if receipted_value is None:
            return "%2s%013.6f" % (code.value, value)
        else:
            return "%2s%013.6fT%013.6f" % (code.value, value, receipted_value)

    def value(self):
        """Return the value of the transaction"""
        return self._value

    def receipted_value(self):
        """Return the receipted value of the transaction. This may be
           different to value() when the transaction was provisional,
           and the receipted value is less than the provisional value
        """
        return self._receipted_value

    def is_credit(self):
        """Return whether or not this is a credit"""
        return self._code == TransactionCode.CREDIT

    def is_debit(self):
        """Return whether or not this is a debit"""
        return self._code == TransactionCode.DEBIT

    def is_liability(self):
        """Return whether or not this is a liability"""
        return self._code == TransactionCode.CURRENT_LIABILITY

    def is_accounts_receivable(self):
        """Return whether or not this is accounts receivable"""
        return self._code == TransactionCode.ACCOUNT_RECEIVABLE

    def is_sent_receipt(self):
        """Return whether or not this is a sent receipt"""
        return self._code == TransactionCode.SENT_RECEIPT

    def is_received_receipt(self):
        """Return whether or not this is a received receipt"""
        return self._code == TransactionCode.RECEIVED_RECEIPT

    def is_sent_refund(self):
        """Return whether or not this is a sent refund"""
        return self._code == TransactionCode.SENT_REFUND

    def is_received_refund(self):
        """Return whether or not this is a received refund"""
        return self._code == TransactionCode.RECEIVED_REFUND
