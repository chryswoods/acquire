
from Acquire.Identity import Authorisation

from Acquire.Service import push_is_running_service, pop_is_running_service, \
    get_service_account_bucket, is_running_service
from Acquire.Crypto import PrivateKey, PublicKey, get_private_key

import pytest
import uuid


@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    try:
        return get_service_account_bucket()
    except:
        d = tmpdir_factory.mktemp("objstore")
        push_is_running_service()
        bucket = get_service_account_bucket(str(d))
        while is_running_service():
            pop_is_running_service()

        return bucket


def test_authorisation(bucket):
    push_is_running_service()

    try:
        key = get_private_key("testing")

        resource = uuid.uuid4()

        auth = Authorisation(resource=resource, testing_key=key)

        auth.assert_once()

        with pytest.raises(PermissionError):
            auth.assert_once()

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
            new_auth.assert_once()

        with pytest.raises(PermissionError):
            new_auth.verify(resource=wrong_resource)
    except:
        pop_is_running_service()
        raise

    pop_is_running_service()
