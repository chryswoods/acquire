
import pytest
import os
import sys
import re

from Acquire.Service import call_function, RemoteFunctionCallError
from Acquire.Client import User
from Acquire.Crypto import OTP


def test_login_fails(aaai_services):
    # register two users
    username1 = "fail1"
    password1 = "Fail1!!!"
    username2 = "fail2"
    password2 = "Fail2!!!"

    user1 = User(username1, identity_url="identity")
    user2 = User(username2, identity_url="identity")

    (provisioning_uri1, qrcode) = user1.register(password1)
    (provisioning_uri2, qrcode) = user2.register(password2)

    assert(qrcode is not None)
    assert(type(provisioning_uri1) is str)
    assert(type(provisioning_uri2) is str)

    # extract the shared secret from the provisioning URI
    otpsecret = re.search(r"secret=([\w\d+]+)&issuer",
                          provisioning_uri1).groups()[0]

    user_otp1 = OTP(otpsecret)

    otpsecret = re.search(r"secret=([\w\d+]+)&issuer",
                          provisioning_uri2).groups()[0]

    user_otp2 = OTP(otpsecret)

    (login_url1, qrcode) = user1.request_login()
    (login_url2, qrcode) = user2.request_login()

    assert(type(login_url1) is str)
    assert(type(login_url2) is str)

    short_uid1 = re.search(r"id=([\w\d+]+)",
                           login_url1).groups()[0]
    short_uid2 = re.search(r"id=([\w\d+]+)",
                           login_url2).groups()[0]

    # try to log in with the wrong user
    args = {}
    args["short_uid"] = short_uid1
    args["username"] = username2
    args["password"] = password2
    args["otpcode"] = user_otp2.generate()

    with pytest.raises(RemoteFunctionCallError):
        call_function("identity", "login", args=args)

    args = {}
    args["short_uid"] = short_uid2
    args["username"] = username1
    args["password"] = password1
    args["otpcode"] = user_otp1.generate()

    with pytest.raises(RemoteFunctionCallError):
        call_function("identity", "login", args=args)

    # now use the right user by the wrong otpcode
    args = {}
    args["short_uid"] = short_uid1
    args["username"] = username1
    args["password"] = password1
    args["otpcode"] = user_otp2.generate()

    with pytest.raises(RemoteFunctionCallError):
        call_function("identity", "login", args=args)

    args = {}
    args["short_uid"] = short_uid2
    args["username"] = username2
    args["password"] = password2
    args["otpcode"] = user_otp1.generate()

    with pytest.raises(RemoteFunctionCallError):
        call_function("identity", "login", args=args)

    # now use the right user by the wrong password
    args = {}
    args["short_uid"] = short_uid1
    args["username"] = username1
    args["password"] = password2
    args["otpcode"] = user_otp1.generate()

    with pytest.raises(RemoteFunctionCallError):
        call_function("identity", "login", args=args)

    args = {}
    args["short_uid"] = short_uid2
    args["username"] = username2
    args["password"] = password1
    args["otpcode"] = user_otp2.generate()

    with pytest.raises(RemoteFunctionCallError):
        call_function("identity", "login", args=args)

    user1.logout()
    user2.logout()
