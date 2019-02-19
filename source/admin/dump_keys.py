
from Acquire.Service import get_this_service, create_return_value, \
    save_service_keys_to_objstore
from Acquire.Identity import Authorisation


def run(args):
    """Call this function to force the service to save its keys
       to the object store
    """
    status = 0
    message = None

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        raise PermissionError(
            "Only an authorised admin can dump the keys")

    service = get_this_service(need_private_access=True)
    service.assert_admin_authorised(
            authorisation, "dump_keys %s" % service.uid())

    save_service_keys_to_objstore(include_old_keys=True)

    status = 0
    message = "Success. Keys have been dumped"

    return_value = create_return_value(status, message)

    return return_value
