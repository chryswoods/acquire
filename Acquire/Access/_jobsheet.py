
__all__ = ["JobSheet"]


class JobSheet:
    """This class holds a complete record of a job that the access
       service has been asked to perform.
    """
    def __init__(self, job=None, authorisation=None):
        if job is not None:
            from Acquire.Identity import Authorisation as _Authorisation
            if not isinstance(authorisation, _Authorisation):
                raise TypeError("You can only authorise a request with "
                                "a valid Authorisation object")

            from Acquire.Access import RunRequest as _RunRequest
            if not isinstance(job, _RunRequest):
                raise TypeError(
                    "You must pass in a valid RunRequest to request a "
                    "calculation is run. The passed request is the wrong "
                    "type: %s" % str(job))

            authorisation.verify(job.fingerprint())
            from Acquire.ObjectStore import create_uid as _create_uid
            self._job = job
            self._authorisation = authorisation
            self._uid = _create_uid()
            self._status = "awaiting"
        else:
            self._uid = None
            self._status = None

        self._credit_notes = None

    def is_null(self):
        """Return whether or not this JobSheet is null

        Returns:
            bool: True if uid is set, False otherwise

        """
        return self._uid is None

    def uid(self):
        """Return the UID of this JobSheet"""
        return self._uid

    def status(self):
        """Return the status of this job"""
        if self.is_null():
            return None
        else:
            return self._status

    def storage_service(self):
        """Return the storage service that will be used to store
           the output data associated with this job

           TODO - will eventually have to choose which storage service
                  to use. Currently returning the storage service that
                  is at the same root URL as this access service
        """
        from Acquire.Service import get_this_service as _get_this_service
        from Acquire.Service import get_trusted_service as _get_trusted_service
        service = _get_this_service()
        storage_url = service.canonical_url().replace("access", "storage")
        return _get_trusted_service(service_url=storage_url)

    def compute_service(self):
        """Return the compute service that will be used to actually
           perform the calculation associated with the job

           TODO - will eventually have to choose which compute service
                  to use. Currently returning the compute service that
                  is at the same root URL as this access service
        """
        from Acquire.Service import get_this_service as _get_this_service
        from Acquire.Service import get_trusted_service as _get_trusted_service
        service = _get_this_service()
        compute_url = service.canonical_url().replace("access", "compute")
        return _get_trusted_service(service_url=compute_url)

    def total_cost(self):
        """Return the total maximum quoted cost for this job. The
           total cost to run the job must not exceed this

           TODO - will need to actually work out and return the
                  real cost - returning dummy values for the moment
        """
        if self.is_null():
            return 0
        else:
            return 10

    def job(self):
        """Return the original job request

            Returns:
                None or Request: If no uid set None, else job request

        """
        if self.is_null():
            return None
        else:
            return self._job

    def authorisation(self):
        """Return the original authorisation for this job"""
        if self.is_null():
            return None
        else:
            return self._authorisation

    def user_guid(self):
        """Return the GUID of the user who requested this job"""
        if self.is_null():
            return None
        else:
            return self._authorisation.user_guid()

    def execute(self, cheque):
        """Execute (start) this job, using the passed cheque for
           payment. Note that you can't start the same job twice
        """
        if self.is_null():
            from Acquire.Accounting import PaymentError
            raise PaymentError("You cannot try to execute a null job!")

        from Acquire.Client import Cheque as _Cheque
        if not isinstance(cheque, _Cheque):
            raise TypeError("You must pass a valid Cheque as payment "
                            "for a job")

        if self._credit_notes is not None:
            raise PermissionError("You cannot start a job twice!")

        from Acquire.Service import get_this_service as _get_this_service

        access_service = _get_this_service(need_private_access=True)
        compute_service = self.compute_service()
        storage_service = self.storage_service()
        accounting_service = cheque.accounting_service()

        access_user = access_service.login_service_user()

        account_uid = access_service.service_user_account_uid(
                                    accounting_service=accounting_service)

        from Acquire.Client import Account as _Account
        access_account = _Account(user=access_user, account_uid=account_uid,
                                  accounting_service=accounting_service)

        # TODO - validate that the cost of the job on the compute
        #        and storage services is covered by the passed cheque

        try:
            credit_notes = cheque.cash(spend=self.total_cost(),
                                       resource=self.job().fingerprint())
        except Exception as e:
            from Acquire.Service import exception_to_string
            from Acquire.Accounting import PaymentError
            raise PaymentError(
                "Problem cashing the cheque used to pay for the calculation: "
                "\n\nCAUSE: %s" % exception_to_string(e))

        if credit_notes is None or len(credit_notes) == 0:
            from Acquire.Accounting import PaymentError
            raise PaymentError("Cannot be paid!")

        # make sure that we have been paid!
        for credit_note in credit_notes:
            if credit_note.credit_account_uid() != access_account.uid():
                raise PaymentError("The wrong account has been paid!?!")

        self._status = "awaiting (paid)"
        self._credit_notes = credit_notes

        # work out when this job MUST have finished. If the job
        # has not completed before this time then it will be killed
        from Acquire.ObjectStore import get_datetime_future \
            as _get_datetime_future

        job_endtime = _get_datetime_future(days=2)  # this should be calculated

        # save the JobSheet to the object store so we don't lose the
        # value in the credit notes
        self.save()

        compute_cheque = _Cheque.write(
                                account=access_account,
                                resource="job %s" % self.uid(),
                                max_spend=10.0,
                                recipient_url=compute_service.canonical_url(),
                                expiry_date=job_endtime)

        storage_cheque = _Cheque.write(
                                account=access_account,
                                resource="job %s" % self.uid(),
                                max_spend=10.0,
                                recipient_url=storage_service.canonical_url(),
                                expiry_date=job_endtime)

        self._compute_cheque = compute_cheque
        self._storage_cheque = storage_cheque

        # TODO - should I save the cheques with the jobsheet?

        # now create a Drive on the storage service that will hold
        # the output for this job
        from Acquire.Client import Drive as _Drive
        from Acquire.Client import StorageCreds as _StorageCreds
        from Acquire.Client import ACLRule as _ACLRule
        from Acquire.Client import ACLRules as _ACLRules
        from Acquire.Client import ACLUserRules as _ACLUserRules

        creds = _StorageCreds(user=access_user,
                              storage_service=storage_service)

        rule = _ACLUserRules.owner(user_guid=access_user.guid()).add(
                    user_guid=self.user_guid(), rule=_ACLRule.reader())

        aclrules = _ACLRules(rule=rule, default_rule=_ACLRule.denied())

        output_drive = _Drive(name="job_output_%s" % self.uid(),
                              creds=creds, aclrules=aclrules,
                              cheque=storage_cheque,
                              max_size="10MB",
                              autocreate=True)

        self._output_loc = output_drive.metadata().location()
        self._status = "awaiting (paid, have drive)"
        self.save()

        from Acquire.Client import PAR as _PAR
        par = _PAR(location=self._output_loc, user=access_user,
                   aclrule=_ACLRule.writer(),
                   expires_datetime=job_endtime)

        secret = compute_service.encrypt_data(par.secret())

        args = {"job_uid": self.uid(),
                "job": self.job().to_data(),
                "output_par": par.to_data(),
                "par_secret": secret,
                "cheque": compute_cheque.to_data()}

        self._status = "submitting"
        self.save()

        response = compute_service.call_function(function="submit_job",
                                                 args=args)

        self._status = "submitted"
        self.save()

        # the service user will log out automatically on destruction, but
        # let us make sure!
        access_user.logout()

        # TODO - should collect something from the response that
        #        can be saved in the job sheet so that we know
        #        how submission is going...

    def output_location(self):
        """Return the location where the output will be saved"""
        if self.is_null():
            return None
        else:
            return self._output_loc

    def save(self):
        """Save this JobSheet to the object store
            Returns:
                None
        """
        from Acquire.Service import assert_running_service \
            as _assert_running_service

        _assert_running_service()

        if self.is_null():
            return

        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        key = "jobsheets/%s" % self.uid()
        _ObjectStore.set_object_from_json(bucket, key, self.to_data())

    @staticmethod
    def load(uid):
        """Return the JobSheet with specified uid loaded from the
           ObjectStore

            Returns:
                JobSheet: an instance of a JobSheet with the specified uid

        """
        from Acquire.Service import assert_running_service \
            as _assert_running_service

        _assert_running_service()

        if uid is None:
            return

        from Acquire.Service import get_service_account_bucket \
            as _get_service_account_bucket

        bucket = _get_service_account_bucket()

        from Acquire.ObjectStore import ObjectStore as _ObjectStore

        key = "jobsheets/%s" % str(uid)
        data = _ObjectStore.get_object_from_json(bucket, key)
        return JobSheet.from_data(data)

    def to_data(self):
        """Get a JSON-serialisable dictionary of this object"""
        data = {}

        if self.is_null():
            return data

        from Acquire.ObjectStore import list_to_string as _list_to_string

        data["uid"] = self.uid()

        try:
            data["job"] = self.job().to_data()
        except:
            pass

        try:
            data["authorisation"] = self.authorisation().to_data()
        except:
            pass

        try:
            data["credit_notes"] = _list_to_string(self._credit_notes)
        except:
            pass

        data["status"] = self._status

        try:
            data["output_location"] = self._output_loc.to_string()
        except:
            pass

        return data

    @staticmethod
    def from_data(data):
        """Return a JobSheet constructed from the passed JSON-deserialised
           dictionary
        """
        if data is None or len(data) == 0:
            return

        j = JobSheet()

        from Acquire.Access import RunRequest as _RunRequest
        from Acquire.Client import Authorisation as _Authorisation
        from Acquire.Client import Location as _Location
        from Acquire.Accounting import CreditNote as _CreditNote
        from Acquire.ObjectStore import string_to_list \
            as _string_to_list

        j._uid = str(data["uid"])

        if "job" in data:
            j._job = _RunRequest.from_data(data["job"])

        if "authorisation" in data:
            j._authorisation = _Authorisation.from_data(
                                            data["authorisation"])

        if "credit_notes" in data:
            j._credit_notes = _string_to_list(data["credit_notes"],
                                              _CreditNote)

        j._status = data["status"]

        if "output_location" in data:
            j._output_loc = _Location.from_string(data["output_location"])

        return j
