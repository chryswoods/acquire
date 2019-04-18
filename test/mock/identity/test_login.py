
import pytest

from Acquire.Service import call_function
from Acquire.Client import User, Wallet
from Acquire.Identity import Authorisation
from Acquire.Crypto import OTP


@pytest.mark.parametrize("username, password",
                         [("testuser", "ABCdef12345"),
                          ("something", "!!DDerfld31"),
                          ("someone", "%$(F*Dj4jij43  kdfjdk")])
def test_login(username, password, aaai_services, tmpdir):
    # register the new user
    result = User.register(username=username,
                           password=password,
                           identity_url="identity")

    assert(type(result) is dict)

    otpsecret = result["otpsecret"]

    user_otp = OTP(otpsecret)

    user = User(username=username, identity_url="identity")
    result = user.request_login()

    assert(type(result) is dict)

    login_url = result["login_url"]

    wallet = Wallet(wallet_dir="%s/acquire_wallet" % tmpdir)
    wallet.send_password(url=login_url, username=username,
                         password=password, otpcode=user_otp.generate(),
                         remember_password=True, remember_device=True,
                         dryrun=True)

    wallet.send_password(url=login_url, username=username,
                         password=password, otpcode=user_otp.generate(),
                         remember_password=True, remember_device=True)

    user.wait_for_login()
    assert(user.is_logged_in())

    auth = Authorisation(user=user, resource="test")

    auth.verify("test")

    user.logout()
