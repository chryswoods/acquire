
import json as _json
import base64 as _base64
import datetime as _datetime
import uuid as _uuid

from ._errors import EncodingError

__all__ = ["bytes_to_string", "string_to_bytes",
           "string_to_encoded", "encoded_to_string",
           "decimal_to_string", "string_to_decimal",
           "datetime_to_string", "string_to_datetime",
           "date_to_string", "string_to_date",
           "time_to_string", "string_to_time",
           "get_datetime_now", "datetime_to_datetime",
           "date_and_time_to_datetime",
           "create_uuid"]


def create_uuid():
    """Return a newly created random uuid. This is highly likely
       to be globally unique
    """
    return str(_uuid.uuid4())


def string_to_encoded(s):
    """Return the passed unicode string encoded to a safely
       encoded base64 utf-8 string"""
    return bytes_to_string(s.encode("utf-8"))


def encoded_to_string(b):
    """Return the passed encoded base64 utf-8 string converted
       back into a unicode string"""
    return string_to_bytes(b).decode("utf-8")


def bytes_to_string(b):
    """Return the passed binary bytes safely encoded to
       a base64 utf-8 string"""
    if b is None:
        return None
    else:
        return _base64.b64encode(b).decode("utf-8")


def string_to_bytes(s):
    """Return the passed base64 utf-8 encoded binary data
       back converted from a string back to bytes. Note that
       this can only convert strings that were encoded using
       bytes_to_string - you cannot use this to convert
       arbitrary strings to bytes"""
    if s is None:
        return None
    else:
        return _base64.b64decode(s.encode("utf-8"))


def decimal_to_string(d):
    """Return the passed decimal number encoded as a string that
       can be safely serialised via json
    """
    return str(d)


def string_to_decimal(s):
    """Return the decimal that had been encoded via 'decimal_to_string'.
       This string must have been created via 'decimal_to_string'
    """
    from Acquire.Accounting import create_decimal as _create_decimal
    return _create_decimal(s)


def datetime_to_string(d):
    """Return the passed datetime encoded to a string. This will be a
       standard iso-formatted time in the UTC timezone (converting
       to UTC if the passed datetime is for another timezone)
    """
    if d.tzinfo is None:
        d = d.replace(tzinfo=_datetime.timezone.utc)
    else:
        d = d.astimezone(_datetime.timezone.utc)

    # the datetime is in UTC, so write out the string without
    # the unnecessary +00:00
    return d.replace(tzinfo=None).isoformat()


def datetime_to_datetime(d):
    """Return the passed datetime as a datetime that is clean
       and usable by Acquire. This will move the datetime to UTC,
       adding the timezone if this is missing
    """
    if not isinstance(d, _datetime.datetime):
        raise TypeError(
            "The passed object '%s' is not a valid datetime" % str(d))

    if d.tzinfo is None:
        return d.replace(tzinfo=_datetime.timezone.utc)
    else:
        return d.astimezone(_datetime.timezone.utc)


def date_and_time_to_datetime(date, time=_datetime.time(0)):
    """Return the passed date and time as a UTC datetime. By
       default the time is midnight (first second of the day)
    """
    return datetime_to_datetime(_datetime.datetime.combine(date, time))


def get_datetime_now():
    """Return the current time in the UTC timezone. This creates an
       object that will be properly stored using datetime_to_string
       and string_to_datetime
    """
    return _datetime.datetime.now(_datetime.timezone.utc)


def string_to_datetime(s):
    """Return the datetime that had been encoded to the passed string
       via datetime_to_string. This string must have been created
       via 'datetime_to_string'
    """
    d = _datetime.datetime.fromisoformat(s)

    if d.tzinfo is None:
        # assume UTC
        d = d.replace(tzinfo=_datetime.timezone.utc)
    else:
        d = d.astimezone(_datetime.timezone.utc)

    return d


def date_to_string(d):
    """Return the date that has been encoded to a string. This will
       write the date as a standard iso-formatted date. IF a datetime
       is passed then this will be in the
       UTC timezone (converting to UTC if the passed datetime
       is for another timezone)
    """
    if isinstance(d, _datetime.datetime):
        return d.astimezone(_datetime.timezone.utc).date().isoformat()
    else:
        return d.isoformat()


def string_to_date(s):
    """Return a date from the string that has been encoded using
       'date_to_string'. This is only guaranteed to work for strings
       that were created using that function
    """
    d = _datetime.date.fromisoformat(s)
    return d


def time_to_string(t):
    """Return the time that has been encoded to a string. This will
       write the time as a standard iso-formatted time. If a datetime
       is passed then this will be in the
       UTC timezone (converting to UTC if the passed datetime
       is for another timezone)
    """
    if isinstance(t, _datetime.datetime):
        if t.tzinfo is None:
            t = t.replace(tzinfo=_datetime.timezone.utc)
        else:
            t = t.astimezone(_datetime.timezone.utc)

        # guaranteed to be in the utc timezone, so write the
        # time without the unnecessary +00:00
        return t.replace(tzinfo=None).time().isoformat()
    else:
        if t.tzinfo is None:
            # assume UTC
            t = t.replace(tzinfo=_datetime.timezone.utc)
        elif t.tzinfo != _datetime.timezone.utc:
            raise EncodingError(
                "Cannot encode a time to a string as this time is "
                "not in the UTC timezone. Please convert to UTC "
                "before encoding this time to a string '%s'" % t.isoformat())

        # as the time is in UTC, we don't need the unnecessary +00:00
        return t.replace(tzinfo=None).isoformat()


def string_to_time(s):
    """Return a time from the string that was encoded by 'time_to_string'.
       This will only be guaranteed to produce valid output for strings
       produced using that function
    """
    t = _datetime.time.fromisoformat(s)

    if t.tzinfo is None:
        # assume this is a UTC time
        t = t.replace(tzinfo=_datetime.timezone.utc)
    else:
        t = t.astimezone(_datetime.timezone.utc)

    return t
