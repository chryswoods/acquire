
import json as _json
import base64 as _base64
import datetime as _datetime
import uuid as _uuid
import os as _os
import sys as _sys

if _sys.version_info.major < 3:
    raise ImportError("Acquire requires Python 3.6 minimum")

if _sys.version_info.minor < 6:
    raise ImportError("Acquire requires Python 3.6 minimum")

if _sys.version_info.major == 3 and _sys.version_info.minor == 6:
    try:
        from backports.datetime_fromisoformat import MonkeyPatch \
            as _MonkeyPatch
        _MonkeyPatch.patch_fromisoformat()
    except:
        raise ImportError(
            "backports-datetime-fromisoformat must be installed "
            "on Python < 3.7. Please run 'pip install "
            "backports-datetime-fromisoformat' or update to a newer "
            "version of Python")

__all__ = ["bytes_to_string", "string_to_bytes",
           "string_to_encoded", "encoded_to_string",
           "url_to_encoded", "encoded_to_url",
           "decimal_to_string", "string_to_decimal",
           "datetime_to_string", "string_to_datetime",
           "date_to_string", "string_to_date",
           "time_to_string", "string_to_time",
           "get_datetime_now", "datetime_to_datetime",
           "string_to_safestring", "safestring_to_string",
           "string_to_list", "list_to_string",
           "string_to_dict", "dict_to_string",
           "string_to_filepath", "string_to_filepath_parts",
           "get_datetime_future",
           "get_datetime_now_to_string",
           "date_and_time_to_datetime",
           "date_and_hour_to_datetime",
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


def url_to_encoded(url):
    """Return an encoding of the passed url that is safe to use
       as a name, filename or key in an object store
    """
    return _base64.b64encode(url.encode("utf-8")).decode("utf-8")


def encoded_to_url(e):
    """Decode the passed encoded data back to the URL. This will only
       produce valid output for inputs created using url_to_encoded
    """
    return _base64.b64decode(e.encode("utf-8")).decode("utf-8")


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


def string_to_decimal(s, default=0):
    """Return the decimal that had been encoded via 'decimal_to_string'.
       This string must have been created via 'decimal_to_string'
    """
    from Acquire.Accounting import create_decimal as _create_decimal
    return _create_decimal(s, default=default)


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


def date_and_hour_to_datetime(date, hour):
    """Return the passed date and hour as a UTC datetime. By
       default the time is hour:00:00 (first second of the hour)
    """
    return datetime_to_datetime(
                _datetime.datetime.combine(date,
                                           _datetime.time(hour=hour)))


def get_datetime_now():
    """Return the current time in the UTC timezone. This creates an
       object that will be properly stored using datetime_to_string
       and string_to_datetime
    """
    return datetime_to_datetime(_datetime.datetime.now(
                                _datetime.timezone.utc))


def get_datetime_now_to_string():
    """Convenience function that returns the result of get_datetime_now
       as a string converted via datetime_to_string
    """
    return datetime_to_string(get_datetime_now())


def get_datetime_future(weeks=0, days=0, hours=0, minutes=0, seconds=0,
                        timedelta=None):
    """Return the datetime that is the supplied time in the future.
       This will raise an exception if the time is not in the future!
    """
    delta = _datetime.timedelta(weeks=weeks, days=days, hours=hours,
                                minutes=minutes, seconds=seconds)

    if timedelta is not None:
        if not isinstance(timedelta, _datetime.timedelta):
            raise TypeError("The delta must be a datetime.timedelta object")

        delta += timedelta

    if delta.total_seconds() < 5:
        raise ValueError(
            "The requested delta (%s) is not sufficiently far enough "
            "into the future!" % str(delta))

    return get_datetime_now() + delta


def string_to_datetime(s):
    """Return the datetime that had been encoded to the passed string
       via datetime_to_string. This string must have been created
       via 'datetime_to_string'
    """
    if isinstance(s, _datetime.datetime):
        return s
    else:
        d = _datetime.datetime.fromisoformat(s)
        return datetime_to_datetime(d)


def date_to_string(d):
    """Return the date that has been encoded to a string. This will
       write the date as a standard iso-formatted date. IF a datetime
       is passed then this will be in the
       UTC timezone (converting to UTC if the passed datetime
       is for another timezone)
    """
    if isinstance(d, _datetime.datetime):
        return datetime_to_datetime(d).date().isoformat()
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
        t = datetime_to_datetime(t)

        # guaranteed to be in the utc timezone, so write the
        # time without the unnecessary +00:00
        return t.replace(tzinfo=None).time().isoformat()
    else:
        if t.tzinfo is None:
            # assume UTC
            t = t.replace(tzinfo=_datetime.timezone.utc)
        elif t.tzinfo != _datetime.timezone.utc:
            from Acquire.ObjectStore import EncodingError
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


def string_to_safestring(s):
    """Return a safe (base64) encoded version of 's'. This string
       has no special characters or spaces, thereby making it safe
       for use, e.g. as a filename or to save in a database
    """
    return _base64.b64encode(s.encode("utf-8")).decode("utf-8")


def safestring_to_string(s):
    """Return the original string encoded by string_to_safestring"""
    return _base64.b64decode(s.encode("utf-8")).decode("utf-8")


def list_to_string(l):
    """Return the passed list of items converted to a json string.
       All items should have the same type
    """
    j = []
    for item in l:
        j.append(item.to_data())

    return _json.dumps(j)


def string_to_list(s, C):
    """Convert the string encoded using list_to_string back to a list
        of objects of type C. Note that all objects must have the
        same type
    """
    items = []

    for val in _json.loads(s):
        items.append(C.from_data(val))

    return items


def dict_to_string(d):
    """Return the passed dict of items converted to a json string.
       All items should have the same type
    """
    j = {}
    for key, value in d.items():
        if value is None:
            j[key] = None
        else:
            j[key] = value.to_data()

    return _json.dumps(j)


def string_to_dict(s, C):
    """Convert the string encoded using dict_to_string back to a dict
        of objects of type C. Note that all objects must have the
        same type
    """
    items = {}

    for key, value in _json.loads(s).items():
        if value is None:
            items[key] = None
        else:
            items[key] = C.from_data(value)

    return items


def string_to_filepath(path):
    """This function cleans the passed path so that doesn't contain
       redundant slashes or '..' etc., so that all backslashes are forwards
       slashes, and that the trailing slash is removed
    """
    if path is None:
        return ""

    path = _os.path.normpath(path)

    # remove all ".." and "." from this path
    if path.find(".") != -1:
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == ".":
                parts[i] = None
            elif part == "..":
                if i == 0:
                    raise ValueError("You cannot start a path with '..'")
                part[i-1] = None
                part[i] = None

        path = _os.path.normpath("/".join(parts))

    return path


def string_to_filepath_parts(path):
    """Break the passed path into a list of the individual parts,
       e.g. /home/user/test/../something/./new.txt will return

       ['home', 'user', 'something', 'new.txt']
    """
    from os.path import split as _split

    path = string_to_filepath(path)

    dirs = []

    (root, part) = _split(path)

    dirs.append(part)

    while len(root) > 0:
        (root, part) = _split(root)

        if len(part) > 0:
            dirs.insert(0, part)
        else:
            break

    return dirs
