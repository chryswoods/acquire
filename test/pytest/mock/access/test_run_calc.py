
import pytest


def test_run_calc(aaai_services, authenticated_user):
    user = authenticated_user

    assert(user.is_logged_in())
