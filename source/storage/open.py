
from Acquire.Service import create_return_value
from Acquire.Service import login_to_service_account
from Acquire.Service import call_function
from Acquire.Service import Service

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes


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

    new_bucket = ObjectStore.create_bucket(bucket, "test_bucket",
        "ocid1.compartment.oc1..aaaaaaaatlvutbwbc6675hnhmueefnl6pvhlpugjixkjt27atmj2a4z3xjaq")

    ObjectStore.set_string_object(new_bucket, "test", "Hello World!")

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    return return_value
