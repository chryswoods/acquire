
from Acquire.Service import ServiceError as _ServiceError

__all__ = ["StorageServiceError"]


class StorageServiceError(_ServiceError):
    pass
