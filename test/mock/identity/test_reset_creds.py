import pytest

from Acquire.Service import call_function
from Acquire.Client import User, Wallet
from Acquire.Identity import Authorisation
from Acquire.Crypto import OTP, PrivateKey

_wallet_password = PrivateKey.random_passphrase()


def test_reset_creds(aaai_services, tmpdir):
    username = "test_rest_creds"
    password = "this is a bad password"

    # register the new user
    result = User.register(username=username,
                           password=password,
                           identity_url="identity")

    otp = result["otp"]

    # now login as the user
    user = User(username=username, identity_url="identity",
                auto_logout=False)

    result = user.request_login()

    login_url = result["login_url"]

    wallet = Wallet()
    wallet.send_password(url=login_url, username=username,
                         password=password, otpcode=otp.generate(),
                         remember_password=True)

    user.wait_for_login()
    assert(user.is_logged_in())

    # now fetch the OTP
    new_otp = user.recover_otp(password=password, reset_otp=False)
    new_otp = new_otp["otp"]

    print(new_otp.generate(), otp.generate())

    assert(otp == new_otp)

    # now reset the OTP
    new_otp = user.recover_otp(password=password, reset_otp=True)
    new_otp = new_otp["otp"]

    print(new_otp.generate(), otp.generate())

    assert(otp != new_otp)

    user.logout()

    # ensure we can log in again...
    otp = new_otp
    user = User(username=username, identity_url="identity",
                auto_logout=False)

    result = user.request_login()

    login_url = result["login_url"]

    wallet = Wallet()
    wallet.send_password(url=login_url, username=username,
                         password=password, otpcode=otp.generate(),
                         remember_password=True)

    user.wait_for_login()
    assert(user.is_logged_in())

    # now fetch the OTP
    new_otp = user.recover_otp(password=password, reset_otp=False)
    new_otp = new_otp["otp"]

    print(new_otp.generate(), otp.generate())

    assert(otp == new_otp)
