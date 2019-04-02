
import pytest

from Acquire.Crypto import PrivateKey
from Acquire.Service import pack_arguments, unpack_arguments

import random


def test_json_keys():
    privkey = PrivateKey()
    pubkey = privkey.public_key()

    args = {"message": "Hello, this is a message",
            "status": 0,
            "long": [random.random() for _ in range(1000)]}

    packed = pack_arguments(args)

    crypted = pubkey.encrypt(packed)

    uncrypted = privkey.decrypt(crypted)

    unpacked = unpack_arguments(uncrypted)

    assert(args == unpacked)
