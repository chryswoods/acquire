
from Acquire.Registry import Registry
from Acquire.Crypto import PublicKey, PrivateKey
from Acquire.ObjectStore import string_to_bytes, bytes_to_string
from Acquire.Service import Service, get_this_service


def run(args):
    """Call this function to register a new service with this registry"""

    service = Service.from_data(args["service"])
    challenge = string_to_bytes(args["challenge"])
    fingerprint = args["fingerprint"]

    # respond to the challenge from the service to be registered
    this_service = get_this_service(need_private_access=True)
    key = this_service.get_key(fingerprint)
    response = key.decrypt(challenge)

    # now challenge the service
    challenge = PrivateKey.random_passphrase()
    pubkey = service.public_key()
    encrypted_challenge = pubkey.encrypt(challenge)

    args = {"challenge": bytes_to_string(encrypted_challenge),
            "fingerprint": pubkey.fingerprint()}

    result = service.call_function(function=None, args=args)

    if result["response"] != challenge:
        raise PermissionError(
            "Failure of the service being registered to correctly respond "
            "to the challenge!")

    challenged_service = Service.from_data(result["service_info"])

    if challenged_service.uid() != "STAGE1":
        raise PermissionError(
            "We cannot create a UID for a service which is "
            "already registered!")

    # this is a new service which has survived challenge, so can
    # now be registered
    registry = Registry()

    service_uid = registry.register_service(service)

    return {"service_uid": service_uid,
            "response": response}
