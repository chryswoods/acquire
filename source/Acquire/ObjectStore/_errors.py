

__all__ = ["ObjectStoreError", "MutexTimeoutError", "PARError",
           "PARTimeoutError", "PARPermissionsError",
           "PARReadError", "PARWriteError"]


class ObjectStoreError(Exception):
    pass


class MutexTimeoutError(Exception):
    pass


class PARError(Exception):
    pass


class PARTimeoutError(PARError):
    pass


class PARPermissionsError(PARError):
    pass


class PARReadError(PARError):
    pass


class PARWriteError(PARError):
    pass
