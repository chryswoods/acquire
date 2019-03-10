

import pytest

from Acquire.Client import Service, Authorisation


def test_create_par(authenticated_user):

    service = Service("storage")

    print(service)

    auth = Authorisation(resource="UserDrives", user=authenticated_user)

    function = "open_drive"

    args = {"authorisation": auth.to_data(),
            "name": "test a drive å∫ç∂"}

    response = service.call_function(function=function, args=args)

    print(response)

    assert(False)
