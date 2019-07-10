
__all__ = ["ComputeJob"]


class ComputeJob:
    """This class holds all information about a compute job. It is used
       as part of record keeping in the compute service, and to pass
       information between the compute service and the actual
       compute cluster
    """
    def __init__(self):
        self._uid = None

    def __str__(self):
        if self.is_null():
            return "ComputeJob::null"
        else:
            return "ComputeJob(uid=%s, request=%s, output=%s)" % (
                self._uid, self._request, self._par.location().to_string())

    def __repr__(self):
        return self.__str__()

    def is_null(self):
        return self._uid is None

    def uid(self):
        """Return the UID of this job"""
        return self._uid

    def request(self):
        """Return the request associated with this job"""
        if self.is_null():
            return None
        else:
            return self._request

    @staticmethod
    def submit(worksheet_uid, request, par, secret, cheque):
        """Submit a job which has;
           worksheet_uid -

        """
        from Acquire.Service import get_this_service as _get_this_service
        from Acquire.Access import RunRequest as _RunRequest
        from Acquire.Client import PAR as _PAR
        from Acquire.Client import Cheque as _Cheque
        from Acquire.ObjectStore import create_uid as _create_uid
        from Acquire.Compute import Cluster as _Cluster

        if not isinstance(request, _RunRequest):
            raise TypeError("The request must be type RunRequest")

        if not isinstance(par, _PAR):
            raise TypeError("The PAR must be type PAR")

        if not isinstance(cheque, _Cheque):
            raise TypeError("The cheque must be type Cheque")

        service = _get_this_service(need_private_access=True)
        cluster = _Cluster.get_cluster()

        job = ComputeJob()

        job._secret = cluster.encrypt_data(service.decrypt_data(secret))
        job._par = par
        job._request = request

        cost = 10  # TODO - calculate cost of job again from request

        try:
            credit_notes = cheque.cash(spend=cost,
                                       resource="work %s" % worksheet_uid)
        except Exception as e:
            from Acquire.Service import exception_to_string
            from Acquire.Accounting import PaymentError
            raise PaymentError(
                "Problem cashing the cheque used to pay for the calculation: "
                "\n\nCAUSE: %s" % exception_to_string(e))

        if credit_notes is None or len(credit_notes) == 0:
            from Acquire.Accounting import PaymentError
            raise PaymentError("Cannot be paid!")

        job._credit_notes = credit_notes

        job._uid = _create_uid(include_date=True, short_uid=True,
                               separator="/")

        job.save()

        # signal server running on cluster to fetch job and actually
        # submit to slurm
        cluster.submit_job(job._uid)

        return job

    def save(self):
        """Save this ComputeJob to the objectstore"""
        if self.is_null():
            return

        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()
        key = "compute/job/%s" % self._uid

        _ObjectStore.set_object_from_json(bucket, key, self.to_data())

    @staticmethod
    def load(uid):
        """Load the ComputeJob associated with the specified uid"""
        from Acquire.ObjectStore import ObjectStore as _ObjectStore
        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()
        key = "compute/job/%s" % uid

        try:
            data = _ObjectStore.get_object_from_json(bucket, key)
        except:
            data = None

        if data is None:
            raise KeyError("There is no job with UID = %s" % uid)

        return ComputeJob.from_data(data)

    def to_data(self):
        """Serialise this job to a json-serialisable dictionary"""
        if self.is_null():
            return {}

        from Acquire.ObjectStore import list_to_string as _list_to_string

        data = {}
        data["uid"] = self._uid
        data["credit_notes"] = _list_to_string(self._credit_notes)
        data["par"] = self._par.to_data()
        data["secret"] = self._secret
        data["request"] = self._request.to_data()

        return data

    @staticmethod
    def from_data(data):
        """Return a ComputeJob constructed from a json-deserialised
           dictionary
        """
        if data is None or len(data) == 0:
            return ComputeJob()

        from Acquire.ObjectStore import string_to_list as _string_to_list
        from Acquire.Access import RunRequest as _RunRequest
        from Acquire.Client import PAR as _PAR
        from Acquire.Accounting import CreditNote as _CreditNote

        job = ComputeJob()

        job._uid = str(data["uid"])
        job._credit_notes = _string_to_list(data["credit_notes"], _CreditNote)
        job._par = _PAR.from_data(data["par"])
        job._secret = str(data["secret"])
        job._request = _RunRequest.from_data(data["request"])

        return job
