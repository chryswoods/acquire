
from Acquire.Identity import Authorisation

from Acquire.Crypto import PrivateKey, PublicKey

import pytest
import uuid


def test_authorisation():
    key = PrivateKey()

    resource = uuid.uuid4()

    auth = Authorisation(resource=resource, testing_key=key)

    auth.verify(resource=resource, testing_key=key.public_key())

    wrong_key = PrivateKey()

    with pytest.raises(PermissionError):
        auth.verify(resource=resource,
                    testing_key=wrong_key.public_key())

    wrong_resource = uuid.uuid4()

    with pytest.raises(PermissionError):
        auth.verify(resource=wrong_resource, testing_key=key.public_key())

    data = auth.to_data()

    new_auth = Authorisation.from_data(data)

    new_auth.verify(resource=resource, testing_key=key.public_key())

    with pytest.raises(PermissionError):
        new_auth.verify(resource=resource,
                        testing_key=wrong_key.public_key())

    with pytest.raises(PermissionError):
        new_auth.verify(resource=wrong_resource, testing_key=key.public_key())
