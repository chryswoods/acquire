
import pytest
import json
import random

from Acquire.ObjectStore import create_uuid

from Acquire.Identity import LoginSession

from Acquire.Crypto import Hash

from Acquire.Client import Credentials


@pytest.mark.parametrize("username, password",
                         [("chrys", "12345Password"),
                          ("me@somewhere.com", "r4u90 fije2j4 w'DDDD"),
                          ("this is my name", "F $O£P ROWF KPD"),
                          ("∆˚´ø ˚ç ¬¬¬¬", "∆∆#ª^  ˚∂ß¬¬ß¬ß˚çççç")])
def test_credentials(username, password):
    identity_uid = create_uuid()
    session_uid = create_uuid()

    if random.randint(0, 1):
        device_uid = create_uuid()
    else:
        device_uid = None

    short_uid = LoginSession.to_short_uid(session_uid)

    otpcode = "%06d" % random.randint(1, 999999)

    data = Credentials.package(identity_uid=identity_uid,
                               short_uid=short_uid,
                               device_uid=device_uid,
                               username=username,
                               password=password,
                               otpcode=otpcode)

    creds = Credentials.unpackage(data=data,
                                  username=username,
                                  short_uid=short_uid)

    assert(creds["username"] == username)
    assert(creds["short_uid"] == short_uid)

    if device_uid is None:
        assert(creds["device_uid"] != device_uid)
    else:
        assert(creds["device_uid"] == device_uid)

    encoded_password = Credentials.encode_password(identity_uid=identity_uid,
                                                   device_uid=device_uid,
                                                   password=password)

    assert(creds["password"] == encoded_password)
    assert(creds["otpcode"] == otpcode)
