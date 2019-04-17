
__all__ = ["get_public_certs"]


def get_public_certs(identity_url, session_uid,
                     scope=None, permissions=None):
    """Call the identity_url to obtain the public keys
       and certificates of the user logged
       in using the specified session_uid. Optionally limit
       the scope and permissions for which these certs would
       be valid
    """
    from Acquire.Service import get_trusted_service as _get_trusted_service

    service = _get_trusted_service(identity_url)

    function = "get_keys"
    args = {"session_uid": session_uid}

    if scope is not None:
        args["scope"] = scope

    if permissions is not None:
        args["permissions"] = permissions

    response = service.call_function(function=function, args=args)

    public_key = None
    public_cert = None

    from Acquire.Crypto import PublicKey as _PublicKey

    if "public_key" in response:
        public_key = _PublicKey.from_data(response["public_key"])

    if "public_cert" in response:
        public_cert = _PublicKey.from_data(response["public_certificate"])

    return (public_key, public_cert)
