
from Acquire.Service import create_return_value
from Acquire.Service import get_checked_remote_service_info, trust_service
from Acquire.Service import get_service_info, create_service_user_account

from Acquire.Crypto import PublicKey
from Acquire.Identity import Authorisation

from Acquire.Service import ServiceAccountError


def run(args):
    """Call this function to trust the passed accounting service,
       specifically to trust that we can move money using that service.
       Note that we must have already trusted the passed accounting
       service as a service before we can trust it as an accounting
       service...
    """
    status = 0
    message = None

    try:
        service_url = args["service_url"]
    except:
        service_url = None

    try:
        public_cert = PublicKey.from_data(args["public_certificate"])
    except:
        public_cert = None

    authorisation = Authorisation.from_data(args["authorisation"])

    accounting_service = get_checked_remote_service_info(service_url,
                                                         public_cert)

    if not accounting_service.is_accounting_service():
        raise ServiceAccountError(
            "%s is not an accounting service, so should not be "
            "trusted as one" % str(accounting_service))

    service = get_service_info(need_private_access=True)
    service.assert_admin_authorised(
        authorisation,
        "trust_accounting_service %s" % accounting_service.uid())

    # compare this service to one we already know
    try:
        check_service = service.get_trusted_service(service_url)
    except Exception as e:
        raise ServiceAccountError(
            "The accounting service must already be trusted as a service "
            "before you can trust it an accounting service! Error=%s" %
            (str(e)))

    if check_service.uid() != accounting_service.uid():
        raise ServiceAccountError(
            "Something strange is happening - the accounting service "
            "appears to have changed since it was trusted? "
            "%s versus %s" % (str(check_service), str(accounting_service)))

    create_service_user_account(service, accounting_service.canonical_url())

    status = 0
    message = "Success. Now trusting %s" % str(service)

    return_value = create_return_value(status, message)

    return_value["args"] = args

    return return_value
