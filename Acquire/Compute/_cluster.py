
from enum import Enum as _Enum

__all__ = ["Cluster"]


class JobState(_Enum):
    PENDING = "pending"
    SUBMITTING = "submitting"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    TERMINATED = "terminated"
    COMPLETED = "completed"


class Cluster:
    """This class provides a handle to the unique compute
       cluster associated with a Compute service. There is only
       one cluster associated with a service, and this
       class provides the handle and functions used to communicate
       between the compute function service and the actual
       compute cluster.

       This class has two sides. On the compute service it provides
       the means to communicate with the cluster. On the cluster
       it provides the means to manage jobs and communicate with
       the compute service.
    """
    def __init__(self):
        self._uid = None

    def is_null(self):
        return self._uid is None

    def fingerprint(self):
        """Return a fingerprint of this cluster, suitable for
           authorisations
        """
        return self.uid()

    def passphrase(self, resource):
        """Generate a passphrase for the passed resource. This is used
           by the client running on the cluster to validate that it is
           allowed to communicate with the cluster on the service
        """
        if self.is_null():
            raise PermissionError(
                "You cannot generate a passphrase from a null Cluster")

        from Acquire.Crypto import Hash as _Hash
        return _Hash.multi_md5(self._secret, resource)

    def verify_passphrase(self, resource, passphrase):
        """Verify that the passed passphrase is correct for the specified
           resource. This is used on the service to validate that a request
           for a resource came from the Cluster running on the client
        """
        if self.is_null():
            raise PermissionError(
                "Invalid passphrase as this is a null Cluster")

        if passphrase != self.passphrase(resource):
            raise PermissionError(
                "Invalid passphrase for resource %s" % resource)

    def compute_service(self):
        """Return the compute service from which this cluster is managed"""
        if self.is_null():
            return None
        elif Cluster._is_running_service():
            from Acquire.Service import get_this_service as _get_this_service
            return _get_this_service()
        else:
            return self._compute_service

    @staticmethod
    def _is_running_service():
        """Return whether or not this is the Cluster on the compute
           service (otherwise it must be on the client)
        """
        from Acquire.Service import is_running_service as _is_running_service
        return _is_running_service()

    @staticmethod
    def create(service_url=None, service_uid=None, user=None):
        """Create a new cluster"""
        if Cluster._is_running_service():
            raise PermissionError(
                "You cannot create a Cluster on a running service")

        from Acquire.Client import PrivateKey as _PrivateKey
        from Acquire.ObjectStore import create_uid as _create_uid
        from Acquire.Client import Wallet as _Wallet

        wallet = _Wallet()
        compute_service = wallet.get_service(service_url=service_url,
                                             service_uid=service_uid)

        if not compute_service.is_compute_service():
            raise TypeError(
                "You can only create a cluster that will communicate "
                "with a valid compute service - not %s" % compute_service)

        cluster = Cluster()
        cluster._uid = _create_uid()
        cluster._private_key = _PrivateKey()
        cluster._public_key = cluster._private_key.public_key()
        cluster._compute_service = compute_service
        cluster._secret = _PrivateKey.random_passphrase()
        cluster._oldkeys = []

        if user is not None:
            Cluster.set_cluster(cluster=cluster, user=user)

        return cluster

    @staticmethod
    def get_cluster():
        """Return a handle to the single compute cluster that is
           connected to this compute service
        """
        if not Cluster._is_running_service():
            raise PermissionError(
                "You can only call 'get_cluster' on the compute service")

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
    def set_cluster(cluster, authorisation=None, passphrase=None, user=None):
        """Function used to set the single compute cluster that is
           connected to this compute service. This must be authorised
           by an admin user of this compute service
        """
        if not isinstance(cluster, Cluster):
            raise TypeError("The cluster must be type Cluster")

        resource = "set_cluster %s" % cluster.fingerprint()

        from Acquire.Client import Authorisation as _Authorisation
        if Cluster._is_running_service():
            from Acquire.Service import get_this_service as _get_this_service

            service = _get_this_service(need_private_access=True)

            if authorisation is not None:
                if not isinstance(authorisation, _Authorisation):
                    raise TypeError(
                        "The authorisation must be type Authorisation")

                service.assert_admin_authorised(authorisation, resource)
            else:
                # we are rotating keys, so check the passphrase against
                # the old passphrase
                cluster = Cluster.get_cluster()
                cluster.verify_passphrase(passphrase=passphrase,
                                          resource="set_cluster")

            from Acquire.ObjectStore import ObjectStore as _ObjectStore
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket

            bucket = _get_service_account_bucket()
            key = "compute/cluster"
            _ObjectStore.set_object_from_json(bucket, key, cluster.to_data())
        else:
            authorisation = _Authorisation(user=user, resource=resource)
            compute_service = cluster.compute_service()

            args = {"authorisation": authorisation.to_data(),
                    "cluster": cluster.to_data()}

            compute_service.call_function(function="set_cluster", args=args)

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

    def rotate_keys(self):
        """Call this function to rotate the cluster keys. This is worth
           performing periodically to ensure that the system remains
           secure - this will also rotate the cluster secret
        """
        if self.is_null():
            return

        if Cluster._is_running_service():
            raise PermissionError("Only the client Cluster can rotate keys")

        passphrase = self.passphrase("set_cluster")

        from Acquire.Crypto import PrivateKey as _PrivateKey
        self._oldkeys.append(self._private_key)

        self._private_key = _PrivateKey()
        self._public_key = self._private_key.public_key()
        self._secret = _PrivateKey.random_passphrase()

        args = {"passphrase": passphrase,
                "cluster": self.to_data()}

        self.compute_service().call_function(function="set_cluster",
                                             args=args)

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

        key = self.private_key()

        try:
            i = len(self._oldkeys)
        except:
            i = 0

        while fingerprint != key.fingerprint():
            i = i-1
            if i < 0:
                from Acquire.Crypto import DecryptionError
                raise DecryptionError(
                    "Cannot decrypt the data as we don't recognise the "
                    "fingerprint of the encryption key: %s" % fingerprint)

            key = self._oldkeys[i]

        data = key.decrypt(data)
        return _json.loads(data)

    def get_job(self, uid, start_state="pending", end_state=None,
                passphrase=None):
        """Return the job with specified 'uid' in the specified
           state (start_state) - this will move the job to
           'end_state' if this is specified. If you are on the
           service you need to supply a valid passphrase
        """
        if end_state is None:
            resource = "get_job %s %s" % (uid, start_state)
        else:
            resource = "get_job %s %s->%s" % (uid, start_state, end_state)

        if Cluster._is_running_service():
            self.verify_passphrase(resource=resource, passphrase=passphrase)

            start_state = JobState(start_state)

            if end_state is not None:
                end_state = JobState(end_state)

            from Acquire.ObjectStore import ObjectStore as _ObjectStore
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket

            bucket = _get_service_account_bucket()
            key = "compute/%s/%s" % (start_state.value, uid)

            if (end_state is None) or (end_state == start_state):
                try:
                    data = _ObjectStore.get_object_from_json(bucket=bucket,
                                                             key=key)
                except:
                    data = None
            else:
                from Acquire.ObjectStore import get_datetime_now_to_string \
                    as _get_datetime_now_to_string

                try:
                    data = _ObjectStore.take_object_from_json(bucket=bucket,
                                                              key=key)
                    data[end_state.value] = _get_datetime_now_to_string()
                    key = "compute/%s/%s" % (end_state.value, uid)
                    _ObjectStore.set_object_from_json(bucket=bucket, key=key,
                                                      data=data)
                except:
                    data = None

            if data is None:
                raise KeyError(
                    "There is no job with UID %s in state %s" %
                    (uid, start_state.value))

            # the data is a dictionary of the submission time and the
            # job UID
            if uid != data["uid"]:
                raise ValueError("The job info for UID %s is corrupt? %s" %
                                 (uid, data))

            # now load the actual job info
            from Acquire.Compute import ComputeJob as _ComputeJob
            return _ComputeJob.load(uid=uid)
        else:
            passphrase = self.passphrase(resource)
            args = {"uid": str(uid),
                    "passphrase": passphrase,
                    "start_state": str(start_state)}

            if end_state is not None:
                args["end_state"] = str(end_state)

            result = self.compute_service().call_function(function="get_job",
                                                          args=args)

            from Acquire.Compute import ComputeJob as _ComputeJob
            return _ComputeJob.from_data(self.decrypt_data(result["job"]))

    def submit_job(self, uid):
        """Submit the job with specified UID to this cluster.

           On the service this will put the UID of the job into the
           "pending" pool, and will signal the cluster to pull that job

           On the client this will pull the job with that UID from the
           pending pool, moving it to the "submitting" pool and will
           pass this job to the cluster submission system
        """
        if Cluster._is_running_service():
            from Acquire.ObjectStore import ObjectStore as _ObjectStore
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket
            from Acquire.ObjectStore import get_datetime_now_to_string \
                as _get_datetime_now_to_string

            bucket = _get_service_account_bucket()
            key = "compute/pending/%s" % uid
            resource = {"pending": _get_datetime_now_to_string(),
                        "uid": uid}

            _ObjectStore.set_object_from_json(bucket, key, resource)
        else:
            # fetch the pending job and change the status to "submitting"
            return self.get_job(uid=uid, start_state="pending",
                                end_state="submitting")

    def get_pending_job_uids(self, passphrase=None):
        """Return the UIDs of all of the jobs that need to be submitted"""
        if self.is_null():
            return []

        if Cluster._is_running_service():
            from Acquire.ObjectStore import ObjectStore as _ObjectStore
            from Acquire.Service import get_service_account_bucket \
                as _get_service_account_bucket

            self.verify_passphrase(resource="get_pending_job_uids",
                                   passphrase=passphrase)

            bucket = _get_service_account_bucket()
            prefix = "compute/pending/"

            uids = _ObjectStore.get_all_object_names(bucket=bucket,
                                                     prefix=prefix,
                                                     without_prefix=True)

            return uids
        else:
            passphrase = self.passphrase(resource="get_pending_job_uids")
            args = {"passphrase": passphrase}
            result = self.compute_service().call_function(
                            function="get_pending_job_uids", args=args)

            return self.decrypt_data(result["job_uids"])

    def to_data(self, passphrase=None):
        """Return a json-serialisable dictionary of this cluster"""
        if self.is_null():
            return {}

        data = {}

        data["uid"] = str(self._uid)
        data["public_key"] = self._public_key.to_data()
        data["secret"] = str(self._secret)

        if passphrase is not None:
            try:
                data["private_key"] = self._private_key.to_data(
                                                    passphrase=passphrase)
            except:
                pass

            try:
                oldkeys = []
                for key in self._oldkeys:
                    oldkeys.append(key.to_data(passphrase=passphrase))

                data["oldkeys"] = oldkeys
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
        cluster._secret = str(data["secret"])

        if passphrase is not None:
            try:
                cluster._private_key = _PrivateKey.from_data(
                                                    data["private_key"],
                                                    passphrase=passphrase)
            except:
                pass

            if "oldkeys" in data:
                try:
                    oldkeys = data["oldkeys"]
                    cluster._oldkeys = []

                    for key in oldkeys:
                        key = _PrivateKey.from_data(key, passphrase=passphrase)
                        cluster._oldkeys.append(key)
                except:
                    pass

        return cluster
