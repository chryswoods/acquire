
__all__ = ["Cluster"]


class Cluster:
    """This class provides a handle to the unique compute
       cluster associated with a Compute service. There is only
       one cluster associated with a service, and this
       class provides the handle and functions used to communicate
       between the compute function service and the actual
       compute cluster
    """
    def __init__(self):
        self._uid = None

    def is_null(self):
        return self._uid is None

    @staticmethod
    def create():
        """Create a new cluster"""
        from Acquire.Client import PrivateKey as _PrivateKey
        from Acquire.ObjectStore import create_uid as _create_uid

        cluster = Cluster()
        cluster._uid = _create_uid()
        cluster._private_key = _PrivateKey()
        cluster._public_key = cluster._private_key.public_key()

    @staticmethod
    def get_cluster():
        """Return a handle to the single compute cluster that is
           connected to this compute service
        """
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()
        key = "compute/cluster"

        try:
            data = _ObjectStore.get_object_from_json(bucket, key)
        except:
            data = None

        if data is None:
            from Acquire.Service import ServiceError
            raise ServiceError(
                "You have not set the cluster that will be used to actually "
                "run the compute jobs!")

        return Cluster.from_data(data)

    @staticmethod
    def set_cluster(cluster, authorisation):
        """Function used to set the single compute cluster that is
           connected to this compute service. This must be authorised
           by an admin user of this compute service
        """
        from Acquire.Client import Authorisation as _Authorisation
        from Acquire.Service import get_this_service as _get_this_service

        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The authorisation must be type Authorisation")

        service = _get_this_service(need_private_access=True)
        service.assert_admin_authorised(
                    authorisation,
                    "set_cluster %s" % cluster.fingerprint())

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()
        key = "compute/cluster"
        _ObjectStore.set_object_from_json(bucket, key, cluster.to_data())

    def uid(self):
        """Return the UID of this cluster"""
        return self._uid

    def public_key(self):
        """Return the public encryption key for this cluster"""
        if self.is_null():
            return None
        else:
            return self._public_key

    def private_key(self):
        """Return the private key for this cluster (if available)"""
        if self.is_null():
            return None
        else:
            try:
                return self._private_key
            except:
                pass

            raise PermissionError(
                "You do not have permission to see the private key of "
                "this cluster")

    def encrypt_data(self, data):
        """Encrypt the passed data so that only the daemon running on
           the cluster can decrypt it. This will be encrypted as;

           data = {"cluster_uid" : "CLUSTER_UID",
                   "fingerprint" : "KEY_FINGERPRINT",
                   "encrypted_data" : "ENCRYPTED_DATA"}
        """
        if self.is_null():
            raise PermissionError("You cannot encrypt using a null cluster!")

        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
        import json as _json
        return {"cluster_uid": str(self.uid()),
                "fingerprint": str(self.public_key().fingerprint()),
                "encrypted_data": _bytes_to_string(
                                 self.public_key().encrypt(_json.dumps(data)))
                }

    def decrypt_data(self, data):
        """Decrypt the pased data - this will only work in the daemon
           running on the cluster itself. The data must have been
           encrypted using the 'encrypt_data' function of this object.
        """
        if self.is_null():
            raise PermissionError("You cannot decrypt using a null cluster!")

        import json as _json

        if isinstance(data, str):
            data = _json.loads(data)

        try:
            from Acquire.ObjectStore import string_to_bytes as _string_to_bytes
            cluster_uid = data["cluster_uid"]
            fingerprint = data["fingerprint"]
            data = _string_to_bytes(data["encrypted_data"])
        except Exception as e:
            from Acquire.Crypto import DecryptionError
            raise DecryptionError(
                "The encrypted data is not of the correct format: %s" % str(e))

        if cluster_uid != self.uid():
            from Acquire.Crypto import DecryptionError
            raise DecryptionError(
                "Cannot decrypt the data as it wasn't encrypted for this "
                "cluster - unmatched cluster UID: %s versus %s" %
                (cluster_uid, self.uid()))

        if fingerprint != self.private_key().fingerprint():
            from Acquire.Crypto import DecryptionError
            raise DecryptionError(
                "Cannot decrypt the data as we don't recognise the "
                "fingerprint of the encryption key: %s versus %s" %
                (fingerprint, self.private_key().fingerprint()))

        data = self.private_key().decrypt(data)
        return _json.loads(data)

    def submit_job(self, uid):
        """Submit the job with specified UID to this cluster. This will
           put the UID of the job into the "pending" pool, and will
           signal the cluster to pull that job
        """
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket
        from Acquire.Service import get_this_service as _get_this_service
        from Acquire.ObjectStore import get_datetime_now_to_string \
            as _get_datetime_now_to_string

        bucket = _get_service_account_bucket()
        key = "compute/pending/%s" % uid

        service = _get_this_service(need_private_access=True)

        resource = "%s %s" % (_get_datetime_now_to_string(), uid)
        resource = service.sign_data(resource)

        _ObjectStore.set_object_from_json(bucket, key, resource)

    def to_data(self, passphrase=None):
        """Return a json-serialisable dictionary of this cluster"""
        if self.is_null():
            return {}

        data = {}

        data["uid"] = str(self._uid)
        data["public_key"] = self._public_key.to_data()

        try:
            data["private_key"] = self._private_key.to_data(
                                                passphrase=passphrase)
        except:
            pass

        return data

    @staticmethod
    def from_data(data, passphrase=None):
        """Return a cluster from the passed json-deserialised data"""
        if data is None or len(data) == 0:
            return Cluster()

        from Acquire.Client import PrivateKey as _PrivateKey
        from Acquire.Client import PublicKey as _PublicKey

        cluster = Cluster()
        cluster._uid = str(data["uid"])
        cluster._public_key = _PublicKey.from_data(data["public_key"])

        try:
            cluster._private_key = _PrivateKey.from_data(data["private_key"],
                                                         passphrase=passphrase)
        except:
            pass

        return cluster
