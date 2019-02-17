
from Acquire.Service import create_return_value
from Acquire.Service import get_service_account_bucket
from Acquire.Service import call_function
from Acquire.Service import Service

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes


class RequestBucketError(Exception):
    pass


def run(args):
    """This function is used to request access to a bucket for
       data in the object store. The user can request read-only
       or read-write access. Access is granted based on a permission
       list
    """

    status = 0
    message = None

    access_token = None

    user_uuid = args["user_uuid"]
    identity_service_url = args["identity_service"]

    # log into the central access account
    bucket = get_service_account_bucket()

    # is the identity service supplied by the user one that we trust?
    identity_service = Service.from_data(
                        ObjectStore.get_object_from_json(
                            bucket,
                            "services/%s" % identity_service_url))

    if not identity_service:
        raise RequestBucketError(
                "You cannot request a bucket because "
                "this access service does not know or trust your supplied "
                "identity service (%s)" % identity_service_url)

    if not identity_service.is_identity_service():
        raise RequestBucketError(
            "You cannot request a bucket because "
            "the passed service (%s) is not an identity service. It is "
            "a %s" %
            (identity_service_url, identity_service.service_type()))

    # Since we trust this identity service, we can ask it to give us the
    # public certificate and signing certificate for this user.
    key = PrivateKey()

    response = call_function(identity_service_url, "get_user_keys",
                             args_key=identity_service.public_key(),
                             response_key=key,
                             user_uuid=user_uuid)

    status = 0
    message = "Success: Status = %s" % str(response)

    return_value = create_return_value(status, message)

    if access_token:
        return_value["access_token"] = access_token

    return return_value
