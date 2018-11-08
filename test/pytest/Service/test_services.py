
import pytest

from Acquire.Service import get_remote_service_info

skip_slow = True


@pytest.mark.slow
def test_login_to_service():
    if skip_slow:
        return

    root_url = "http://130.61.60.88:8080/t"

    identity_service_url = "%s/identity" % root_url
    access_service_url = "%s/access" % root_url
    accounting_service_url = "%s/accounting" % root_url

    identity_service = get_remote_service_info(identity_service_url)

    # check whois
    username = "chryswoods"

    (get_username, uid) = identity_service.whois(username=username)

    assert(username == get_username)

    (get_username, get_uid) = identity_service.whois(user_uid=uid)

    assert(username == get_username)
    assert(uid == get_uid)

    access_service_url = get_remote_service_info(access_service_url)
    accounting_service_url = get_remote_service_info(accounting_service_url)
