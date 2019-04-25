
import pytest

import random
import os

from Acquire.Crypto import PublicKey, PrivateKey, SymmetricKey, \
                           SignatureVerificationError


def test_keys():
    privkey = PrivateKey()
    pubkey = privkey.public_key()

    assert(privkey.fingerprint() == pubkey.fingerprint())

    message = "Hello World"

    sig = privkey.sign(message)
    pubkey.verify(sig, message)

    c = pubkey.encrypt(message)

    m = privkey.decrypt(c)
    assert(m == message)

    privkey2 = PrivateKey()
    sig2 = privkey2.sign(message)

    with pytest.raises(SignatureVerificationError):
        pubkey.verify(sig2, message)

    bytes = privkey.bytes("testPass32")

    PrivateKey.read_bytes(bytes, "testPass32")

    privkey.write("test.pem", "testPass32")

    PrivateKey.read("test.pem", "testPass32")

    bytes = pubkey.bytes()
    pubkey2 = PublicKey.read_bytes(bytes)

    assert(pubkey.fingerprint() == pubkey2.fingerprint())

    assert(bytes == pubkey2.bytes())

    long_message = str([random.getrandbits(8)
                       for _ in range(4096)])

    c = pubkey.encrypt(long_message)

    m = privkey.decrypt(c)

    assert(m == long_message)

    os.unlink("test.pem")

    data = pubkey.to_data()

    pubkey2 = PublicKey.from_data(data)

    assert(pubkey.fingerprint() == pubkey2.fingerprint())
    assert(pubkey.bytes() == pubkey2.bytes())

    data = privkey.to_data("testPass33")

    privkey2 = PrivateKey.from_data(data, "testPass33")

    assert(privkey.fingerprint() == privkey2.fingerprint())
    assert(privkey == privkey2)

    symkey = SymmetricKey()

    c = symkey.encrypt(message)

    assert(message == symkey.decrypt(c))

    c = symkey.encrypt(long_message)

    assert(long_message == symkey.decrypt(c))

    symkey = SymmetricKey("This is a key")

    c = symkey.encrypt(long_message)

    assert(long_message == SymmetricKey("This is a key").decrypt(c))

    data = symkey.to_data("testPass33")

    symkey2 = SymmetricKey.from_data(data, "testPass33")

    assert(symkey.fingerprint() == symkey2.fingerprint())
    assert(symkey == symkey2)

    assert(long_message == symkey2.decrypt(c))
