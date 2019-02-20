
__all__ = ["QRCodeError", "LoginError", "AccountError",
           "PaymentError", "UserError"]


class QRCodeError(Exception):
    pass


class LoginError(Exception):
    pass


class AccountError(Exception):
    pass


class UserError(Exception):
    pass


class PaymentError(Exception):
    pass
