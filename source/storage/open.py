
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

    user_uid = args["user_uid"]
    object_name = args['object_name']
    md5sum = args["md5sum"]

    service = get_service_info()

    if not service.is_storage_service():
        raise ServiceAccountError(
            "We can only perform storage functions using a StorageService...")

    bucket = login_to_service_account()

    # get the bucket used for user data

    try:
        new_bucket = ObjectStore.get_bucket(
                        bucket=bucket, bucket_name="test_bucket",
                        compartment=service.storage_compartment(),
                        create_if_needed=True)
    except Exception as e:
        raise RequestBucketError(
            "Unable to open the bucket 'test_bucket': %s" % str(e))

    # First save an empty object, so that we can then create
    # a PAR that can be used to write the actual data
    ObjectStore.set_object_from_json(new_bucket, "test_key",
                                     None)

    par = ObjectStore.create_par(new_bucket, "test_key",
                                 readable=True, writeable=True)

    par2 = ObjectStore.create_par(new_bucket, readable=False, writeable=True)

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    return_value["test_key"] = ObjectStore.get_object_from_json(new_bucket,
                                                                "test_key")

    return_value["par"] = par.to_data()
    return_value["par2"] = par2.to_data()

    return return_value
