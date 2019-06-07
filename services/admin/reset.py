
import os

from Acquire.Service import get_this_service, get_service_account_bucket

from Acquire.ObjectStore import ObjectStore


def run(args):
    """This function completely resets a service and deletes
       all data. This resets back to the original state.
       Obviously you should be really sure you want to do this!
    """

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        raise PermissionError(
            "Only an authorised admin can reset the service")

    service = get_this_service(need_private_access=True)
    service.assert_admin_authorised(
            authorisation, "reset %s" % service.uid())

    bucket = get_service_account_bucket()

    ObjectStore.delete_all_objects(bucket)
