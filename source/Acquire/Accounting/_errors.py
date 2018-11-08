
from Acquire.Service import ServiceError

__all__ = ["AccountingServiceError", "LedgerError", "TransactionError",
           "AccountError", "UnbalancedLedgerError", "InsufficientFundsError",
           "UnmatchedReceiptError"]


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


class InsufficientFundsError(Exception):
    pass


class UnmatchedReceiptError(Exception):
    pass


class UnmatchedRefundError(Exception):
    pass
