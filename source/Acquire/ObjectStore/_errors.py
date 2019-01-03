

__all__ = ["ObjectStoreError", "MutexTimeoutError", "PARError",
           "PARTimeoutError", "PARPermissionsError"]


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
