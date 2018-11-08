
import pytest

import random
import os

from Acquire.Crypto import PublicKey, PrivateKey, SignatureVerificationError


def test_keys():
    privkey = PrivateKey()
    pubkey = privkey.public_key()

    message = "Hello World"

    sig = privkey.sign(message.encode("utf-8"))
    pubkey.verify(sig, message.encode("utf-8"))

    c = pubkey.encrypt(message.encode("utf-8"))

    m = privkey.decrypt(c).decode("utf-8")
    assert(m == message)

    privkey2 = PrivateKey()
    sig2 = privkey2.sign(message.encode("utf-8"))

    with pytest.raises(SignatureVerificationError):
        pubkey.verify(sig2, message.encode("utf-8"))

    bytes = privkey.bytes("testPass32")

    PrivateKey.read_bytes(bytes, "testPass32")

    privkey.write("test.pem", "testPass32")

    PrivateKey.read("test.pem", "testPass32")

    bytes = pubkey.bytes()
    pubkey2 = PublicKey.read_bytes(bytes)

    assert(bytes == pubkey2.bytes())

    long_message = str([random.getrandbits(8)
                       for _ in range(4096)]).encode("utf-8")

    c = pubkey.encrypt(long_message)

    m = privkey.decrypt(c)

    assert(m == long_message)

    os.unlink("test.pem")

    data = pubkey.to_data()

    pubkey2 = PublicKey.from_data(data)

    assert(pubkey.bytes() == pubkey2.bytes())

    data = privkey.to_data("testPass33")

    privkey2 = PrivateKey.from_data(data, "testPass33")

    assert(privkey == privkey2)
