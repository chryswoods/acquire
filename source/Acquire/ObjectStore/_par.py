
import datetime as _datetime

from ._errors import PARError

__all__ = ["PAR"]


class PAR:
    """This class holds the result of a pre-authenticated request
       (a PAR - also called a pre-signed request). This holds a URL
       at which an object (or entire bucket) in the object store
       can be accessed. The PAR has a lifetime.

       This object can safely be saved and/or transmitted from
       the server to the client
    """
    def __init__(self, url=None, key=None,
                 expires_timestamp=None, is_writeable=False,
                 driver=None):
        """Construct a PAR result by passing in the URL at which the
           object can be accessed, the UTC timestamp when this expires,
           whether this is writeable, and (optionally) 'key' for the
           object that is accessed (if this is not supplied then an
           entire bucket is accessed). If 'is_writeable' then read/write
           access has been granted. Otherwise access is read-only.
           This also records the type of object store behind this PAR
           in the free-form string 'driver'
        """
        self._url = url
        self._key = key
        self._expires_timestamp = expires_timestamp
        self._driver = driver

        if self.seconds_remaining() < 60:
            raise PARError(
                "It is not valid to create a PAR with less than 60 "
                "seconds of validity: %s" % str(self))

        if is_writeable:
            self._is_writeable = True
        else:
            self._is_writeable = False

    def __str__(self):
        if self._key is None:
            return "PAR( bucket=True, url=%s, seconds_remaining=%s )" % \
                (self.url(), self.seconds_remaining())
        else:
            return "PAR( key=%s, url=%s, seconds_remaining=%s )" % \
                (self.key(), self.url(), self.seconds_remaining())

    def url(self):
        """Return the URL at which the bucket/object can be accessed"""
        return self._url

    def is_writeable(self):
        """Return whether or not this PAR gives write access"""
        return self._is_writeable

    def key(self):
        """Return the key for the object this accesses - this is None
           if the PAR grants access to the entire bucket"""
        return self._key

    def is_bucket(self):
        """Return whether or not this PAR is for an entire bucket"""
        return self._key is None

    def is_object(self):
        """Return whether or not this PAR is for a single object"""
        return self._key is not None

    def driver(self):
        """Return the underlying object store driver used for this PAR"""
        return self._driver

    def seconds_remaining(self):
        """Return the number of seconds remaining before this PAR expires.
           This will return 0 if the PAR has already expired. To be safe,
           you should renew PARs if the number of seconds remaining is less
           than 60
        """
        now = _datetime.datetime.utcnow()
        expires = _datetime.datetime.utcfromtimestamp(self._expires_timestamp)

        delta = (expires - now).total_seconds()

        if delta < 0:
            return 0
        else:
            return delta
