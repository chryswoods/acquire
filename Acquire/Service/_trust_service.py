
__all__ = ["trust_service", "untrust_service"]


def trust_service(service, authorisation=None):
    """Trust the passed service. This will record this service as trusted,
       e.g. saving the keys and certificates for this service and allowing
       it to be used for the specified type. You must pass in a valid
       admin_user authorisation for this service
    """
    from Acquire.Service import is_running_service as _is_running_service

    if _is_running_service():
        from Acquire.Service import get_this_service as _get_this_service
        from Acquire.Service import get_service_account_bucket as \
            _get_service_account_bucket
        from Acquire.ObjectStore import url_to_encoded as \
            _url_to_encoded

        from Acquire.Identity import Authorisation as _Authorisation

        if not isinstance(authorisation, _Authorisation):
            raise PermissionError(
                "You must supply a valid authorisation when you want to trust "
                "a new service!")

        local_service = _get_this_service(need_private_access=True)
        local_service.assert_admin_authorised(
            authorisation, "trust_service %s" % service.uid())

        bucket = _get_service_account_bucket()

        urlkey = "_trusted/url/%s" % _url_to_encoded(service.canonical_url())
        uidkey = "_trusted/uid/%s" % service.uid()
        service_data = service.to_data()

        # store the trusted service by both canonical_url and uid
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        _ObjectStore.set_object_from_json(bucket, uidkey, service_data)
        _ObjectStore.set_string_object(bucket, urlkey, uidkey)

        from Acquire.Service import clear_services_cache \
            as _clear_services_cache
        _clear_services_cache()
    else:
        from Acquire.Client import Wallet as _Wallet
        _Wallet.add_service(service)


def untrust_service(service, authorisation=None):
    """Stop trusting the passed service. This will remove the service
       as being trusted. You must pass in a valid admin_user authorisation
       for this service
    """
    from Acquire.Service import is_running_service as _is_running_service

    if _is_running_service():
        from Acquire.Service import get_this_service as _get_this_service
        from Acquire.Service import get_service_account_bucket as \
            _get_service_account_bucket
        from Acquire.ObjectStore import url_to_encoded as \
            _url_to_encoded

        from Acquire.Identity import Authorisation as _Authorisation

        if not isinstance(authorisation, _Authorisation):
            raise PermissionError(
                "You must supply a valid authorisation when you want to "
                "stop trusting a service!")

        local_service = _get_this_service(need_private_access=True)
        local_service.assert_admin_authorised(
            authorisation, "untrust_service %s" % service.uid())

        bucket = _get_service_account_bucket()
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

        from Acquire.Service import clear_services_cache \
            as _clear_services_cache
        _clear_services_cache()
    else:
        from Acquire.Client import Wallet as _Wallet
        _Wallet.remove_service(service)
