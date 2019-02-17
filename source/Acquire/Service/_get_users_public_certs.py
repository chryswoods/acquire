
__all__ = ["get_users_public_certs"]


def get_users_public_certs(identity_url, username, session_uid):
    """Call the identity_url to obtain the public keys
       and certificates of the user with 'username' logged
       in using the specified session_uid
    """
    from Acquire.Service import get_trusted_service as _get_trusted_service

    service = _get_trusted_service(identity_url)

    function = "get_keys"
    args = {"username": username,
            "session_uid": session_uid}

    response = service.call_function(function=function, args=args)

    public_key = None
    public_cert = None

    from Acquire.Crypto import PublicKey as _PublicKey
    from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

    if "public_key" in response:
        public_key = _PublicKey.read_bytes(
                          _string_to_bytes(response["public_key"]))

    if "public_cert" in response:
        public_cert = _PublicKey.read_bytes(
                          _string_to_bytes(response["public_cert"]))

    return (public_key, public_cert)
