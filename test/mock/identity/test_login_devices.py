
import pytest

from Acquire.Client import User, Wallet
from Acquire.Crypto import OTP, PrivateKey

_wallet_password = PrivateKey.random_passphrase()


def test_login_devices(aaai_services, tmpdir):
    username = "test_login_devices"
    password = "this is a very bad password"

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

    service = user.identity_service()

    result = service.call_function(function="login_devices",
                                   args={"user_uid": user.uid()})

    print(result)
