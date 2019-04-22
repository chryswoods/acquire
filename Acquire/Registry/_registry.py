
__all__ = ["Registry"]

_registry_key = "registry"


def _inc_uid(vals):
    for j in range(0,len(vals)):
        i = len(vals) - j - 1
        vals[i] += 1

        if i % 2 == 1:
            if vals[i] < 10:
                return vals
            else:
                vals[i] = 0
        else:
            if vals[i] < 52:
                return vals
            else:
                vals[i] = 0

    return vals


def _to_uid(vals):
    import string as _string
    parts = []
    for i in range(0, len(vals)):
        x = vals[i]
        if i % 2 == 1:
            if x < 0 or x > 9:
                raise ValueError(x)
            else:
                parts.append(str(x))
        else:
            if x < 0 or x > 51:
                raise ValueError(x)
            elif x < 26:
                parts.append(_string.ascii_lowercase[x])
            else:
                parts.append(_string.ascii_uppercase[x-26])

    return "".join(parts)


def _generate_service_uid(bucket, registry_uid):
    """Function to generate a new service_uid on this registry"""
    from Acquire.ObjectStore import ObjectStore as _ObjectStore
    from Acquire.ObjectStore import Mutex as _Mutex

    key = "%s/last_service_uid" % _registry_key

    mutex = _Mutex(key=key)

    try:
        last_vals = _ObjectStore.get_object_from_json(bucket=bucket,
                                                      key=key)
        _inc_uid(last_vals)
    except:
        last_vals = [0, 0, 0, 0, 0, 0]

    _ObjectStore.set_object_from_json(bucket=bucket, key=key, data=last_vals)
    mutex.unlock()

    return _to_uid(last_vals)


class Registry:
    """This class holds the registry of all services registered by
       this service. Registries provided trusted actors who
       can supply public keys, URLs, and UIDs for all of the different
       services in the system.
    """
    def __init__(self):
        """Constructor"""
        self._bucket = None

    def get_bucket(self):
        if self._bucket:
            return self._bucket
        else:
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            self._bucket = _get_service_account_bucket()
            return self._bucket

    def registry_uid(self):
        from Acquire.Service import get_this_service as _get_this_service
        return _get_this_service(need_private_access=False).uid()

    def _get_key_for_uid(self, service_uid):
        return "%s/uid/%s" % (_registry_key, service_uid)

    def _get_key_for_url(self, service_url):
        from Acquire.ObjectStore import string_to_encoded \
            as _string_to_encoded
        return "%s/url/%s" % (_registry_key, _string_to_encoded(service_url))

    def get_service_key(self, service_uid=None, service_url=None):
        """Return the key for the passed service in the object store"""
        if service_uid is not None:
            return self._get_key_for_uid(service_uid)
        else:
            bucket = self.get_bucket()
            key = self._get_key_for_url(service_url)

            try:
                from Acquire.ObjectStore import ObjectStore as _ObjectStore
                service_key = _ObjectStore.get_string_object(bucket=bucket,
                                                             key=key)
            except:
                service_key = None

            return service_key

    def get_service(self, service_uid=None, service_url=None):
        """Load and return the service with specified url or uid
           from the registry. This will consult with other
           registry services to find the matching service
        """
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import Service as _Service
        from Acquire.ObjectStore import string_to_encoded \
            as _string_to_encoded
        from Acquire.Service import get_this_service as _get_this_service

        this_service = _get_this_service(need_private_access=False)

        if this_service.uid() == service_uid:
            return this_service
        elif this_service.canonical_url() == service_url:
            return this_service

        bucket = self.get_bucket()

        service_key = self.get_service_key(service_uid=service_uid,
                                           service_url=service_url)

        service = None

        if service_key is not None:
            try:
                data = _ObjectStore.get_object_from_json(bucket=bucket,
                                                         key=service_key)
                service = _Service.from_data(data)
            except:
                pass

        if service is not None:
            if service.uid() == "STAGE1" or service.should_refresh_keys():
                service.refresh_keys()
                data = service.to_data()
                _ObjectStore.set_object_from_json(bucket=bucket,
                                                  key=service_key,
                                                  data=data)
            return service

    def register_service(self, service):
        """Register the passed service"""
        from Acquire.Service import Service as _Service

        if not isinstance(service, _Service):
            raise TypeError("You can only register Service objects")

        if service.uid() != "STAGE1":
            raise PermissionError("You cannot register a service twice!")

        service_uid = _generate_service_uid(bucket=self.get_bucket(),
                                            registry_uid=self.registry_uid())

        return service_uid
