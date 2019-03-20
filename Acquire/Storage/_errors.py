
from Acquire.Service import ServiceError as _ServiceError

__all__ = ["StorageServiceError", "MissingDriveError", "MissingFileError",
           "MissingVersionError"]


class StorageServiceError(_ServiceError):
    pass


class MissingDriveError(Exception):
    pass


class MissingFileError(Exception):
    pass


class MissingVersionError(Exception):
    pass
