

__all__ = ["ObjectStoreError", "MutexTimeoutError", "EncodingError",
           "RequestBucketError"]


class ObjectStoreError(Exception):
    pass


class EncodingError(ObjectStoreError):
    pass


class MutexTimeoutError(Exception):
    pass

class RequestBucketError(Exception):
    pass
