
import pytest
import os
import sys
import re

from Acquire.Service import call_function
from Acquire.Client import User
from Acquire.Crypto import OTP
from Acquire.Client import LoginError, Wallet


def test_login_fails(aaai_services, tmpdir):
    # register two users
    username1 = "fail1"
    password1 = "Fail1!!!"
    username2 = "fail2"
    password2 = "Fail2!!!"

    result = User.register(username=username1,
                           password=password1,
                           identity_url="identity")

    assert(type(result) is dict)

    otp1 = result["otp"]

    user1 = User(username=username1, identity_url="identity",
                 auto_logout=False)

    result = User.register(username=username2,
                           password=password2,
                           identity_url="identity")

    assert(type(result) is dict)

    otp2 = result["otp"]

    user2 = User(username=username2, identity_url="identity",
                 auto_logout=False)

    result1 = user1.request_login()
    result2 = user2.request_login()

    assert(type(result1) is dict)
    assert(type(result2) is dict)

    login_url1 = result1["login_url"]
    login_url2 = result2["login_url"]

    wallet = Wallet()

    # try to log in with the wrong user
    with pytest.raises(LoginError):
        wallet.send_password(url=login_url1, username=username2,
                             password=password2, otpcode=otp2.generate(),
                             remember_password=False, remember_device=False)

    with pytest.raises(LoginError):
        wallet.send_password(url=login_url2, username=username1,
                             password=password1, otpcode=otp1.generate(),
                             remember_password=False, remember_device=False)

    # now use the right user by the wrong otpcode
    with pytest.raises(LoginError):
        wallet.send_password(url=login_url1, username=username1,
                             password=password1, otpcode=otp2.generate(),
                             remember_password=False, remember_device=False)

    # now use the right user by the wrong otpcode
    with pytest.raises(LoginError):
        wallet.send_password(url=login_url2, username=username2,
                             password=password2, otpcode=otp1.generate(),
                             remember_password=False, remember_device=False)

    # now use the right user by the wrong password
    with pytest.raises(LoginError):
        wallet.send_password(url=login_url1, username=username1,
                             password=password2, otpcode=otp1.generate(),
                             remember_password=False, remember_device=False)

    with pytest.raises(LoginError):
        wallet.send_password(url=login_url2, username=username2,
                             password=password1, otpcode=otp1.generate(),
                             remember_password=False, remember_device=False)

    # now, get it right ;-)
    wallet.send_password(url=login_url1, username=username1,
                         password=password1, otpcode=otp1.generate(),
                         remember_password=False, remember_device=False)

    wallet.send_password(url=login_url2, username=username2,
                         password=password2, otpcode=otp2.generate(),
                         remember_password=False, remember_device=False)

    user1.logout()
    user2.logout()
