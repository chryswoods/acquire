
_par_root = "storage/par"


class PARRegistry:
    """This object is used by the storage service to manage
       a registry of all of the active PARs in the service
    """
    def __init__(self):
        pass

    def register(self, par, authorisation, secret=None):
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

        if secret is not None and len(secret) > 0:
            from Acquire.Crypto import Hash
            secret = Hash.multi_md5(uid, secret)
        else:
            secret = None

        import json as _json
        data = {"par": par.to_data(),
                "identifiers": _json.dumps(identifiers),
                "secret": secret}

        key = "%s/%s" % (_par_root, uid)

        bucket = _get_service_account_bucket()
        _ObjectStore.set_object_from_json(bucket, key, data)

        return uid

    def resolve(self, par_uid, secret=None):
        """Resolve the passed PAR and return the corresponding
           DriveMeta or FileMeta with requisite permissions
        """
        # validate that the UID actually looks like a UID. This
        # should prevent attacks that try weird UIDs
        from Acquire.ObjectStore import validate_is_uid \
            as _validate_is_uid
        _validate_is_uid(par_uid)

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        try:
            key = "%s/%s" % (_par_root, par_uid)
            bucket = _get_service_account_bucket()
            data = _ObjectStore.get_object_from_json(bucket, key)

            from Acquire.Client import PAR as _PAR
            import json as _json
            par = _PAR.from_data(data["par"])
            identifiers = _json.loads(data["identifiers"])

            if secret != data["secret"]:
                raise PermissionError()
        except:
            raise PermissionError(
                "There is no valid PAR at ID '%s'" % par_uid)

        print(par)
        print(identifiers)

        if par.expired():
            raise PermissionError(
                "There is no valid PAR at ID '%s' as it has expired" % par_uid)

        from Acquire.Storage import DriveInfo as _DriveInfo
        from Acquire.Storage import DriveMeta as _DriveMeta
        drive = _DriveInfo(drive_uid=par.identifier().drive_uid(),
                           identifiers=identifiers,
                           aclrule=par.aclrule(),
                           is_authorised=True)

        drivemeta = _DriveMeta(uid=drive.uid(),
                               aclrules=drive.aclrules())

        drive_acl = drivemeta.resolve_acl()

        if drive_acl.denied():
            raise PermissionError(
                "The PAR does not have permission to access the drive")

        if par.identifier().is_drive():
            return drivemeta

        filemetas = drive.list_files(par.identifier())

        return filemetas
