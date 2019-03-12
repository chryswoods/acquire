
from Acquire.Service import ServiceError as _ServiceError

__all__ = ["StorageServiceError", "MissingDriveError", "MissingFileError"]


class StorageServiceError(_ServiceError):
    pass


class MissingDriveError(Exception):
    pass


class MissingFileError(Exception):
    pass
