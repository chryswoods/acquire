
from Acquire.Service import ServiceError

__all__ = ["AccountingServiceError", "LedgerError", "TransactionError",
           "AccountError", "UnbalancedLedgerError", "InsufficientFundsError",
           "UnmatchedReceiptError", "PaymentError"]


class AccountingServiceError(ServiceError):
    pass


class AccountError(Exception):
    pass


class LedgerError(Exception):
    pass


class TransactionError(Exception):
    pass


class UnbalancedLedgerError(Exception):
    pass


class PaymentError(Exception):
    pass


class InsufficientFundsError(PaymentError):
    pass


class UnmatchedReceiptError(Exception):
    pass


class UnmatchedRefundError(Exception):
    pass
