
import pytest

from Acquire.Service import call_function
from Acquire.Client import User, Wallet
from Acquire.Identity import Authorisation
from Acquire.Crypto import OTP, PrivateKey
from Acquire.ObjectStore import get_datetime_future

try:
    from freezegun import freeze_time
    have_freezetime = True
except:
    have_freezetime = False

_wallet_password = PrivateKey.random_passphrase()


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

    otp = result["otp"]

    user = User(username=username, identity_url="identity",
                auto_logout=False)

    result = user.request_login()

    assert(type(result) is dict)

    login_url = result["login_url"]

    wallet = Wallet()

    wallet.send_password(url=login_url, username=username,
                         password=password, otpcode=otp.generate(),
                         remember_password=True)

    user.wait_for_login()
    assert(user.is_logged_in())

    auth = Authorisation(user=user, resource="test")

    auth.verify("test")

    user.logout()

    if not have_freezetime:
        # we cannot continue as we need to wait for the old otpcode
        # to expire...
        return

    # now try to log in, using the remembered password
    with freeze_time(get_datetime_future(hours=1)) as _frozen_datetime:
        user = User(username=username, identity_url="identity",
                    auto_logout=False)

        result = user.request_login()

        login_url = result["login_url"]

        # the test has to specify the username as we can't choose...
        wallet.send_password(url=login_url, username=username,
                            otpcode=otp.generate(),
                            remember_device=True)

        user.wait_for_login()
        assert(user.is_logged_in())

        auth = Authorisation(user=user, resource="test")

        auth.verify("test")

        user.logout()

    # now see if the wallet can send all login info
    # now try to log in, using the remembered password
    with freeze_time(get_datetime_future(hours=2)) as _frozen_datetime:
        user = User(username=username, identity_url="identity",
                    auto_logout=False)
        result = user.request_login()

        login_url = result["login_url"]

        # the test has to specify the username as we can't choose...
        wallet.send_password(url=login_url, username=username)

        user.wait_for_login()
        assert(user.is_logged_in())

        auth = Authorisation(user=user, resource="test")

        auth.verify("test")

        user.logout()
