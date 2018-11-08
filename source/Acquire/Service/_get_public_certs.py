

from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

from Acquire.Crypto import PublicKey as _PublicKey

from ._function import call_function as _call_function

__all__ = ["get_public_certs"]


def get_public_certs(identity_url, username, session_uid):
    """Call the identity_url to obtain the public keys
       and certificates of the user with 'username' logged
       in using the specified session_uid
    """

    response = _call_function(identity_url, "get_keys",
                              username=username, session_uid=session_uid)

    public_key = None
    public_cert = None

    if "public_key" in response:
        public_key = _PublicKey.read_bytes(
                          _string_to_bytes(response["public_key"]))

    if "public_cert" in response:
        public_cert = _PublicKey.read_bytes(
                          _string_to_bytes(response["public_cert"]))

    return (public_key, public_cert)
