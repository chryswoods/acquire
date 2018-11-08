

__all__ = ["QRCodeError", "LoginError", "AccountError", "UserError"]


class QRCodeError(Exception):
    pass


class LoginError(Exception):
    pass


class AccountError(Exception):
    pass


class UserError(Exception):
    pass
