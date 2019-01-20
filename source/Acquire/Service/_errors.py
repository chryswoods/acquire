
__all__ = ["AccountError", "PackingError", "UnpackingError",
           "RemoteFunctionCallError", "ServiceError", "ServiceAccountError",
           "MissingServiceAccountError"]


class AccountError(Exception):
    pass


class PackingError(Exception):
    pass


class UnpackingError(Exception):
    pass


class RemoteFunctionCallError(Exception):
    pass


class ServiceError(Exception):
   pass


class ServiceAccountError(Exception):
    pass


class MissingServiceAccountError(Exception):
    pass
