

__all__ = ["ObjectStoreError", "MutexTimeoutError", "PARError"]


class ObjectStoreError(Exception):
    pass


class MutexTimeoutError(Exception):
    pass


class PARError(Exception):
    pass
