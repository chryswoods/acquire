
import pytest
import os
import sys
import re

from Acquire.Service import call_function
from Acquire.Client import User, uid_to_username
from Acquire.Crypto import OTP



@pytest.mark.parametrize("username, password",
                         [("testuser", "ABCdef12345"),
                          ("something", "!!DDerfld31"),
                          ("someone", "%$(F*Dj4jij43  kdfjdk")])
def test_login(username, password, aaai_services):
    # register the new user
    user = User(username, identity_url="identity")

    (provisioning_uri, qrcode) = user.register(password)

    # extract the shared secret from the provisioning URI
    otpsecret = re.search(r"secret=([\w\d+]+)&issuer",
                          provisioning_uri).groups()[0]

    user_otp = OTP(otpsecret)

    # now get and check the whois lookup...
    user_uid = user.uid()
    check_username = uid_to_username(user_uid, identity_url="identity")

    assert(check_username == username)

    (login_url, qrcode) = user.request_login()

    assert(type(login_url) is str)

    short_uid = re.search(r"id=([\w\d+]+)",
                          login_url).groups()[0]

    args = {}
    args["short_uid"] = short_uid
    args["username"] = username
    args["password"] = password
    args["otpcode"] = user_otp.generate()

    result = call_function("identity", "login", args=args)

    assert("status" in result)
    assert(result["status"] == 0)

    user.logout()
