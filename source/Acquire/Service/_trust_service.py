
from ._login_to_objstore import login_to_service_account as \
                               _login_to_service_account

from ._service_account import get_service_info as _get_service_info
from ._get_services import clear_services_cache as _clear_services_cache

from Acquire.ObjectStore import ObjectStore as _ObjectStore
from Acquire.ObjectStore import url_to_encoded as _url_to_encoded

__all__ = ["trust_service", "untrust_service"]


def trust_service(service, authorisation):
    """Trust the passed service. This will record this service as trusted,
       e.g. saving the keys and certificates for this service and allowing
       it to be used for the specified type. You must pass in a valid
       admin_user authorisation for this service
    """
    local_service = _get_service_info(need_private_access=True)
    local_service.assert_admin_authorised(authorisation,
                                          "trust_service %s" % service.uid())

    bucket = _login_to_service_account()
    urlkey = "_trusted/url/%s" % _url_to_encoded(service.canonical_url())
    uidkey = "_trusted/uid/%s" % service.uid()
    service_data = service.to_data()

    # store the trusted service by both canonical_url and uid
    _ObjectStore.set_object_from_json(bucket, uidkey, service_data)
    _ObjectStore.set_string_object(bucket, urlkey, uidkey)

    _clear_services_cache()


def untrust_service(service, authorisation):
    """Stop trusting the passed service. This will remove the service
       as being trusted. You must pass in a valid admin_user authorisation
       for this service
    """
    local_service = _get_service_info(need_private_access=True)
    local_service.assert_admin_authorised(authorisation,
                                          "trust %s" % service.uid())

    bucket = _login_to_service_account()
    urlkey = "_trusted/url/%s" % _url_to_encoded(service.canonical_url())
    uidkey = "_trusted/uid/%s" % service.uid()

    # delete the trusted service by both canonical_url and uid
    try:
        _ObjectStore.delete_object(bucket, uidkey)
    except:
        pass

    try:
        _ObjectStore.delete_object(bucket, urlkey)
    except:
        pass

    _clear_services_cache()
