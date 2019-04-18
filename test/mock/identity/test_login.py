
import pytest

from Acquire.Service import call_function
from Acquire.Client import User, Wallet
from Acquire.Identity import Authorisation
from Acquire.Crypto import OTP, PrivateKey

_wallet_password = PrivateKey.random_passphrase()


@pytest.mark.parametrize("username, password",
                         [("testuser", "ABCdef12345"),
                          ("something", "!!DDerfld31"),
                          ("someone", "%$(F*Dj4jij43  kdfjdk")])
def test_login(username, password, aaai_services, tmpdir):
    # register the new user
    wallet_dir = "%s/acquire_wallet" % tmpdir

    result = User.register(username=username,
                           password=password,
                           identity_url="identity",
                           wallet_dir=wallet_dir)

    assert(type(result) is dict)

    otpsecret = result["otpsecret"]

    user_otp = OTP(otpsecret)

    user = User(username=username, identity_url="identity",
                wallet_dir=wallet_dir, auto_logout=False)

    result = user.request_login()

    assert(type(result) is dict)

    login_url = result["login_url"]

    wallet = Wallet(wallet_dir=wallet_dir, wallet_password=_wallet_password)

    wallet.send_password(url=login_url, username=username,
                         password=password, otpcode=user_otp.generate(),
                         remember_password=True, remember_device=True)

    user.wait_for_login()
    assert(user.is_logged_in())

    auth = Authorisation(user=user, resource="test")

    auth.verify("test")

    user.logout()
