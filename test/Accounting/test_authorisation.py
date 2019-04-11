
from Acquire.Identity import Authorisation

from Acquire.Crypto import PrivateKey, PublicKey

import pytest
import uuid


def test_authorisation():
    key = PrivateKey()

    resource = uuid.uuid4()

    auth = Authorisation(resource=resource, testing_key=key)

    auth.verify(resource=resource)

    wrong_resource = uuid.uuid4()

    with pytest.raises(PermissionError):
        auth.verify(resource=wrong_resource)

    data = auth.to_data()

    new_auth = Authorisation.from_data(data)

    with pytest.raises(PermissionError):
        new_auth.verify(resource=resource)

    new_auth._testing_key = key

    new_auth.verify(resource=resource)

    with pytest.raises(PermissionError):
        new_auth.verify(resource=wrong_resource)
