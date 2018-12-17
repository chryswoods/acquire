
import pytest
import os
import re

from unittest import mock

from Acquire.Crypto import PrivateKey, OTP
from Acquire.Service import login_to_service_account

from identity.request_login import run as request_login
from identity.register import run as register
from identity.setup import run as setup_service


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    try:
        bucket = login_to_service_account()
    except:
        d = tmpdir_factory.mktemp("identity")
        bucket = login_to_service_account(str(d))

    args = {"password": "ABCdef12345",
            "service_url": "localhost:8080"}

    os.environ["SERVICE_PASSWORD"] = "Service_pa33word"
    setup_service(args)

    return bucket


def test_login(bucket):
    # register the new user
    args = {"username": "testuser",
            "password": "ABCdef12345"}

    result = register(args)

    assert("status" in result)
    assert(result["status"] == 0)

    assert("provisioning_uri" in result)
    provisioning_uri = result["provisioning_uri"]

    # extract the shared secret from the provisioning URI
    otpsecret = re.search(r"secret=([\w\d+]+)&issuer",
                           provisioning_uri).groups()[0]

    otp = OTP(otpsecret)
    print(otp)
    print(result)

    session_key = PrivateKey()
    session_cert = PrivateKey()

    args = {"username": "testuser",
            "public_key": session_key.public_key().to_data(),
            "public_certificate": session_cert.public_key().to_data()}

    result = request_login(args)

    print(result)

    assert(False)
