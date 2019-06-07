
from Acquire.Service import get_this_service, refresh_service_keys_and_certs
from Acquire.Identity import Authorisation


def run(args):
    """Call this function to force the service to regenerate its keys

       Args:
            args (dict): contains authorisaton details for key refresh
    """
    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        raise PermissionError(
            "Only an authorised admin can dump the keys")

    service = get_this_service(need_private_access=True)
    service.assert_admin_authorised(
            authorisation, "refresh_keys %s" % service.uid())

    service = refresh_service_keys_and_certs(service=service,
                                             force_refresh=True)

    return_value = {}
    return_value["service_info"] = service.to_data()
