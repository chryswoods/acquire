
from Acquire.Service import ServiceError

__all__ = ["AccessServiceError", "RunRequestError"]


class AccessServiceError(ServiceError):
    pass


class RunRequestError(Exception):
    pass
