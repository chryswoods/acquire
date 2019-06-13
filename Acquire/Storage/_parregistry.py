
_par_root = "storage/par"


class PARRegistry:
    """This object is used by the storage service to manage
       a registry of all of the active PARs in the service
    """
    def __init__(self):
        pass

    def register(self, par, authorisation):
        """Register the passed par, which is authorised using the
           passed authorisation. If the authorisation is correct
           this this will return the URL of the PAR
        """
        from Acquire.Client import PAR as _PAR
        from Acquire.Client import Authorisation as _Authorisation

        if not isinstance(par, _PAR):
            raise TypeError("The par must be type PAR")

        # create a new UID for this PAR
        from Acquire.ObjectStore import create_uid as _create_uid
        uid = _create_uid()
        par._set_uid(uid)

        if par.expired():
            raise PermissionError("The passed PAR has already expired!")

        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The authorisation must be type Authorisation")

        identifiers = authorisation.verify(
                            resource="create_par %s" % par.fingerprint(),
                            return_identifiers=True)

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        import json as _json
        data = {"par": par.to_data(),
                "identifiers": _json.dumps(identifiers)}

        key = "%s/%s" % (_par_root, uid)

        bucket = _get_service_account_bucket()
        _ObjectStore.set_object_from_json(bucket, key, data)

        return uid
