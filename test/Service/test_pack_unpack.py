
import pytest

from Acquire.Crypto import PrivateKey, get_private_key
from Acquire.Service import pack_arguments, unpack_arguments
from Acquire.Service import pack_return_value, unpack_return_value
from Acquire.Service import create_return_value
from Acquire.ObjectStore import string_to_bytes, bytes_to_string

import random
import json


def _bar():
    raise PermissionError("Test Traceback")


def _foo():
    _bar()


def test_pack_unpack_args_returnvals():
    privkey = get_private_key("testing")
    pubkey = privkey.public_key()

    args = {"message": "Hello, this is a message",
            "status": 0,
            "long": [random.random() for _ in range(2)]}

    func = "test_function"

    packed = pack_arguments(function=func, args=args)

    crypted = pubkey.encrypt(packed)

    uncrypted = privkey.decrypt(crypted)

    (f, unpacked, keys) = unpack_arguments(args=uncrypted)

    print(keys)

    assert(args == unpacked)
    assert(f == func)

    packed = pack_arguments(function=func, args=args,
                            key=pubkey, response_key=pubkey,
                            public_cert=pubkey)

    data = json.loads(packed.decode("utf-8"))

    assert(data["encrypted"])
    assert(data["fingerprint"] == privkey.fingerprint())

    payload = privkey.decrypt(string_to_bytes(data["data"]))
    payload = json.loads(payload)

    assert(payload["sign_with_service_key"] == privkey.fingerprint())
    assert(payload["encryption_public_key"] == bytes_to_string(pubkey.bytes()))
    assert(payload["payload"] == args)

    (f, unpacked, keys) = unpack_arguments(function=func, args=packed,
                                           key=privkey)

    message = {"message": "OK"}

    return_value = create_return_value(message)

    packed_result = pack_return_value(function=func,
                                      payload=return_value, key=keys,
                                      private_cert=privkey)

    result = json.loads(packed_result.decode("utf-8"))

    assert(result["fingerprint"] == privkey.fingerprint())
    assert(result["encrypted"])
    data = string_to_bytes(result["data"])
    sig = string_to_bytes(result["signature"])

    pubkey.verify(signature=sig, message=data)

    data = json.loads(privkey.decrypt(data))

    assert(data["payload"]["return"] == message)

    result = unpack_return_value(return_value=packed_result,
                                 key=privkey, public_cert=pubkey)

    assert(result == message)

    try:
        return_value = create_return_value(_foo())
    except Exception as e:
        return_value = create_return_value(e)

    packed_result = pack_return_value(function=func,
                                      payload=return_value, key=keys,
                                      private_cert=privkey)

    with pytest.raises(PermissionError):
        result = unpack_return_value(function=func, return_value=packed_result,
                                     key=privkey, public_cert=pubkey)
