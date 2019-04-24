
__all__ = ["get_registry_details", "update_registry_keys_and_certs"]

_testing_registry = {
    "canonical_url": "registry",
    "uid": "Z9-Z9",
    "public_key": None,
    "public_certificate": None}

_acquire_registry = {
    "canonical_url": "http://fn.acquire-aaai.com:8080/t/registry",
    "uid": "a0-a0",
    "public_key": {"bytes": "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU"
                            "5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FR"
                            "RUF1SE1iMzNUYytTZjFkVFBMMk9ESApqSWcxQjJYMENBeV"
                            "hVMVl4ejI5aWl5cTJlQm5FZGFuQXNTZ2oxS0dYbUJCRHdr"
                            "N2Y4SmJNWDVNOE5hbm9jVXRWClZ2aW1jbm1LZVhRRVQweTh"
                            "VM216NzR2OUZid056azYxdkpNRXhHa0tyVzRjdi81b1dlYU"
                            "FEdmVLSkJ5UzEwYnUKSjlYVU9IZTZIR1B2bWYyelk2QVBkN"
                            "2JCTHFlN3lMVjAvSi93WS9sOGlYNHNtc1gxM2NsY0s4YXpj"
                            "elIzN1pYQQpSQkhkKzlOSllnS2ZqbXB4akxYcWpIN3R4cUh"
                            "RTzNYS3Z3blhiOXlUbVV4TEg2aEdLQ2xiZ2l6RGdCNjRQWD"
                            "dnCk5xb2c2STBFVWl5bEhlNjZ6aXFRcm5QZWVtUjNzNm03T"
                            "2RwS2Y2eU8vd2dmaXpVaVBhSkwvS0xaTHplQXc2RFkKcHdJ"
                            "REFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=="},
    "public_certificate": {"bytes": "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KT"
                                    "UlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0"
                                    "FROEFNSUlCQ2dLQ0FRRUF4RWRvYTlLRUkvS0N"
                                    "zN1UxdGlLTwpwbUN5UVRnU2hBb1lXTW9jTHJWN"
                                    "GFQRStGdVdQYzBlWlRSeEdqSDBJOEN4bXZub2p"
                                    "IYVd2dDN3Tm9Jb2s5b2JICkcwazI3blFnZ05jO"
                                    "EYvWUpKZ1JVcVRkdExDdkFWOEcxRWN5bDQrS1l"
                                    "1UEIzNFpIMTFqUit1V3RqUzAvc2JJbnUKV3JiV"
                                    "WhObFVwemJxbm8yT2UvVXIvSHJOZ2liUXM1eFR"
                                    "Od3BvK2NWMkpiM0NDM21YUkxUWkZpaFMwY1lXN"
                                    "ytLSwoyQ1I5QUM4UnltZ1h3TUUzTXUvT2JYV1F"
                                    "UMk0vSzNlcUJxYkZjUFZLL04zOFhERS8xbnlvR"
                                    "1djTnBsWWNHU3oyCjNrZWhsWUNTVWh1T01tbGt"
                                    "3NkFQMllDR05oRzNXRjdYZUlTdXZvMWovMnlNN"
                                    "2pIY2gzZjZjcWRvWWNLNk5Lc0IKQXdJREFRQUI"
                                    "KLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=="}}

_registries = {_testing_registry["uid"]: _testing_registry,
               _acquire_registry["uid"]: _acquire_registry}


def update_registry_keys_and_certs(registry_uid, public_key,
                                   public_certificate):
    """This function is called to update the registry details stored
       globally with those in the newly-created registry-service. This
       function should only be called by registry services after
       construction
    """
    if registry_uid not in _registries:
        raise PermissionError(
            "Cannot update registry details as this is not one of the "
            "centrally approved registries!")

    from Acquire.Crypto import PublicKey as _PublicKey

    if type(public_key) is not _PublicKey:
        raise TypeError("The public key must be type PublicKey")

    if type(public_certificate) is not _PublicKey:
        raise TypeError("The public certificate must be type PublicKey")

    r = _registries[registry_uid]

    r["public_key"] = public_key.to_data()
    r["public_certificate"] = public_certificate.to_data()

    _registries[registry_uid] = r


def get_registry_details(registry_uid):
    """Return the details for the registry with specified UID.
       Note that this will only return details for the approved
       and centrally-registered registries. This returns
       a dictionary with key registry details.
    """
    try:
        import copy as _copy
        return _copy.copy(_registries[registry_uid])
    except:
        return _copy.copy(_registries["a0-a0"])
