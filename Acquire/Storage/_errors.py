
from Acquire.Service import ServiceError as _ServiceError

__all__ = ["StorageServiceError", "MissingDriveError"]


class StorageServiceError(_ServiceError):
    pass


class MissingDriveError(Exception):
    pass
