
from Acquire.Service import get_this_service, save_service_keys_to_objstore
from Acquire.Identity import Authorisation


def run(args):
    """Call this function to force the service to save its keys
       to the object store

       Args:
            args (dict): contains authorisaton details for key dump

        Returns:
            dict: contains status and status message regarding success
            of key dump operation


    """
    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        raise PermissionError(
            "Only an authorised admin can dump the keys")

    service = get_this_service(need_private_access=True)
    service.assert_admin_authorised(
            authorisation, "dump_keys %s" % service.uid())

    save_service_keys_to_objstore(include_old_keys=True)
