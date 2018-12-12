
from Acquire.Service import create_return_value
from Acquire.Service import login_to_service_account
from Acquire.Service import get_service_info

from Acquire.ObjectStore import ObjectStore, string_to_bytes

from Acquire.Service import ServiceAccountError


class CreateBucketError(Exception):
    pass


class RequestBucketError(Exception):
    pass


def run(args):
    """This function is used to request that a new object(file)
       is opened for writing on the object store. This will create
       a new bucket for the user in which the files will be placed,
       if a bucket for the user does not already exist.
    """

    status = 0
    message = None

    # receive the credit note that shows that the user has paid for
    # this storage. Also parse the request to find the files that
    # need creating and the UID of the user who made the request
    # (so that they can put their files in their own bucket)

    bucket = login_to_service_account()

    service = get_service_info(bucket=bucket)

    if not service.is_storage_service():
        raise ServiceAccountError(
            "We can only perform storage functions using a StorageService...")

    # now create/get handle to the bucket in which we will be placing the
    # new object
    new_bucket = ObjectStore.get_bucket(
                    bucket, bucket_name="test_bucket",
                    compartment=service.storage_compartment(),
                    create_if_needed=True)

    ObjectStore.set_string_object(new_bucket, "test_key", "Hello World!")

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    return_value["test_key"] = ObjectStore.get_string_object(new_bucket,
                                                             "test_key")

    return return_value
