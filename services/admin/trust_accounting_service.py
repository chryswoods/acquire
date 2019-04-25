
from Acquire.Service import get_trusted_service
from Acquire.Service import get_this_service, create_service_user_account

from Acquire.Crypto import PublicKey
from Acquire.Identity import Authorisation

from Acquire.Service import ServiceAccountError


def run(args):
    """Call this function to trust the passed accounting service,
       specifically to trust that we can move money using that service.

       Args:
            args(dict): containing data on the service we want
            to trust

       Returns:
            dict: containing status, status message and passed in args
    """
    service_url = args["service_url"]

    authorisation = Authorisation.from_data(args["authorisation"])

    accounting_service = get_trusted_service(service_url=service_url)

    if not accounting_service.is_accounting_service():
        raise ServiceAccountError(
            "%s is not an accounting service, so should not be "
            "trusted as one" % str(accounting_service))

    service = get_this_service(need_private_access=True)
    service.assert_admin_authorised(
        authorisation,
        "trust_accounting_service %s" % accounting_service.uid())

    url = accounting_service.canonical_url()

    create_service_user_account(service=service, accounting_service_url=url)

    return_value = {}

    return_value["args"] = args

    return return_value
