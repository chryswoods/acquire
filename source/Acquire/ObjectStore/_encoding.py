
import json as _json
import base64 as _base64
import datetime as _datetime
import uuid as _uuid

__all__ = ["bytes_to_string", "string_to_bytes",
           "string_to_encoded", "encoded_to_string",
           "decimal_to_string", "string_to_decimal",
           "datetime_to_string", "string_to_datetime",
           "get_datetime_now", "create_uuid"]


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
    return d.astimezone(_datetime.timezone.utc).isoformat()


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
    return _datetime.datetime.fromisoformat(s)
