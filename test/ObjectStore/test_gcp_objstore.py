import uuid

import pytest

from Acquire.ObjectStore import ObjectStore, ObjectStoreError
from Acquire.ObjectStore._gcp_objstore import GCP_ObjectStore
from Acquire.Service import get_service_account_bucket, \
    push_is_running_service, pop_is_running_service, \
    is_running_service

from unittest.mock import patch, MagicMock

MOCK_UUID = '814c82ae-9ac4-11e9-8cea-ccf696920b49'


@pytest.mark.parametrize("new_gcp_bucket,location,regional", [('new_gcp_bucket', 'europe-west2', 'REGIONAL'),
                                                              (None, 'europe-west2', 'REGIONAL')])
def test_create_bucket(new_gcp_bucket, location, regional):

    with patch('uuid.uuid4', return_value=MOCK_UUID):

        expected_gcp_bucket = new_gcp_bucket
        if not new_gcp_bucket:
            expected_gcp_bucket = MOCK_UUID

        bucket_mock = MagicMock()
        bucket_name = "gcp_bucket"
        bucket_mock.name.return_value = bucket_name
        bucket_mock.location.return_value = location
        client_mock = MagicMock()
        bucket_dict = {'bucket': bucket_mock, 'client': client_mock, 'bucket_name': bucket_name}

        GCP_ObjectStore.create_bucket(bucket_dict, new_gcp_bucket)
        client_mock.call_count == 1
        client_mock.mock_calls[0][0] == "create_bucket"
        new_bucket_obj = client_mock.mock_calls[0][1][0]
        assert new_bucket_obj.location == bucket_mock.location
        assert new_bucket_obj.storage_class == regional
        assert new_bucket_obj.name == expected_gcp_bucket


