
import json as _json

import base64 as _base64

__all__ = ["bytes_to_string", "string_to_bytes",
           "string_to_encoded", "encoded_to_string"]


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
