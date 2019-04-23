
from Acquire.Registry import Registry
from Acquire.Crypto import PublicKey, PrivateKey
from Acquire.ObjectStore import string_to_bytes, bytes_to_string
from Acquire.Service import Service, get_this_service


def run(args):
    """Call this function to register a new service with this registry"""

    service = Service.from_data(args["service"])
    challenge = string_to_bytes(args["challenge"])
    fingerprint = args["fingerprint"]

    try:
        force_new_uid = args["force_new_uid"]
    except:
        force_new_uid = False

    if force_new_uid:
        force_new_uid = True

    # respond to the challenge from the service to be registered
    this_service = get_this_service(need_private_access=True)
    key = this_service.get_key(fingerprint)
    response = key.decrypt(challenge)

    # ok - we can respond to its challenge, so now challenge
    # it, and if it passes, register the service
    registry = Registry()
    service_uid = registry.register_service(service=service,
                                            force_new_uid=force_new_uid)

    return {"service_uid": service_uid,
            "response": response}
