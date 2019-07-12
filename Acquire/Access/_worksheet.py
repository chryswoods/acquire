
__all__ = ["WorkSheet"]


class WorkSheet:
    """This class holds a complete record of the work that the access
       service has been asked to perform.
    """
    def __init__(self, request=None, authorisation=None):
        if request is not None:
            from Acquire.Identity import Authorisation as _Authorisation
            if not isinstance(authorisation, _Authorisation):
                raise TypeError("You can only authorise work with "
                                "a valid Authorisation object")

            from Acquire.Access import RunRequest as _RunRequest
            if not isinstance(request, _RunRequest):
                raise TypeError(
                    "You must pass in a valid RunRequest to request a "
                    "calculation is run. The passed request is the wrong "
                    "type: %s" % str(request))

            authorisation.verify(request.fingerprint())
            from Acquire.ObjectStore import create_uid as _create_uid
            self._request = request
            self._authorisation = authorisation
            self._uid = _create_uid(include_date=True, short_uid=True,
                                    separator="-")
            self._status = "awaiting"
        else:
            self._uid = None
            self._status = None

        self._credit_notes = None

    def is_null(self):
        """Return whether or not this WorkSheet is null"""
        return self._uid is None

    def uid(self):
        """Return the UID of this WorkSheet"""
        return self._uid

    def status(self):
        """Return the status of the work"""
        if self.is_null():
            return None
        else:
            return self._status

    def storage_service(self):
        """Return the storage service that will be used to store
           the output data associated with this work

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
           perform the calculation associated with this work

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
        """Return the total maximum quoted cost for this work. The
           total cost to run the work must not exceed this

           TODO - will need to actually work out and return the
                  real cost - returning dummy values for the moment
        """
        if self.is_null():
            return 0
        else:
            return 10

    def request(self):
        """Return the original work request"""
        if self.is_null():
            return None
        else:
            return self._request

    def authorisation(self):
        """Return the original authorisation for this request"""
        if self.is_null():
            return None
        else:
            return self._authorisation

    def user_guid(self):
        """Return the GUID of the user who requested this work"""
        if self.is_null():
            return None
        else:
            return self._authorisation.user_guid()

    def execute(self, cheque):
        """Execute (start) this work, using the passed cheque for
           payment. Note that you can't perform the same work twice
        """
        if self.is_null():
            from Acquire.Accounting import PaymentError
            raise PaymentError("You cannot try to execute null work!")

        from Acquire.Client import Cheque as _Cheque
        if not isinstance(cheque, _Cheque):
            raise TypeError("You must pass a valid Cheque as payment "
                            "for the work")

        if self._credit_notes is not None:
            raise PermissionError("You cannot start a piece of work twice!")

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

        # TODO - validate that the cost of the work on the compute
        #        and storage services is covered by the passed cheque

        try:
            credit_notes = cheque.cash(spend=self.total_cost(),
                                       resource=self.request().fingerprint())
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

        endtime = _get_datetime_future(days=2)  # this should be calculated

        # save the WorkSheet to the object store so we don't lose the
        # value in the credit notes
        self.save()

        compute_cheque = _Cheque.write(
                                account=access_account,
                                resource="work %s" % self.uid(),
                                max_spend=10.0,
                                recipient_url=compute_service.canonical_url(),
                                expiry_date=endtime)

        storage_cheque = _Cheque.write(
                                account=access_account,
                                resource="work %s" % self.uid(),
                                max_spend=10.0,
                                recipient_url=storage_service.canonical_url(),
                                expiry_date=endtime)

        self._compute_cheque = compute_cheque
        self._storage_cheque = storage_cheque

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

        output_drive = _Drive(name="output_%s" % self.uid(),
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
                   expires_datetime=endtime)

        secret = compute_service.encrypt_data(par.secret())

        args = {"worksheet_uid": self.uid(),
                "request": self.request().to_data(),
                "par": par.to_data(),
                "secret": secret,
                "cheque": compute_cheque.to_data()}

        self._status = "submitting"
        self.save()

        response = compute_service.call_function(function="submit_job",
                                                 args=args)

        print(response)

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
        """Save this WorkSheet to the object store
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

        key = "worksheet/%s" % self.uid()
        _ObjectStore.set_object_from_json(bucket, key, self.to_data())

    @staticmethod
    def load(uid):
        """Return the WorkSheet with specified uid loaded from the
           ObjectStore
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

        key = "worksheet/%s" % str(uid)
        data = _ObjectStore.get_object_from_json(bucket, key)
        return WorkSheet.from_data(data)

    def to_data(self):
        """Get a JSON-serialisable dictionary of this object"""
        data = {}

        if self.is_null():
            return data

        from Acquire.ObjectStore import list_to_string as _list_to_string

        data["uid"] = self.uid()

        try:
            data["request"] = self.request().to_data()
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

        try:
            data["compute_cheque"] = self._compute_cheque.to_data()
        except:
            pass

        try:
            data["storage_cheque"] = self._storage_cheque.to_data()
        except:
            pass

        return data

    @staticmethod
    def from_data(data):
        """Return a WorkSheet constructed from the passed JSON-deserialised
           dictionary
        """
        if data is None or len(data) == 0:
            return

        j = WorkSheet()

        from Acquire.Access import RunRequest as _RunRequest
        from Acquire.Client import Authorisation as _Authorisation
        from Acquire.Client import Location as _Location
        from Acquire.Client import Cheque as _Cheque
        from Acquire.Accounting import CreditNote as _CreditNote
        from Acquire.ObjectStore import string_to_list \
            as _string_to_list

        j._uid = str(data["uid"])

        if "request" in data:
            j._request = _RunRequest.from_data(data["request"])

        if "authorisation" in data:
            j._authorisation = _Authorisation.from_data(
                                            data["authorisation"])

        if "credit_notes" in data:
            j._credit_notes = _string_to_list(data["credit_notes"],
                                              _CreditNote)

        j._status = data["status"]

        if "output_location" in data:
            j._output_loc = _Location.from_string(data["output_location"])

        if "compute_cheque" in data:
            j._compute_cheque = _Cheque.from_data(data["compute_cheque"])

        if "storage_cheque" in data:
            j._storage_cheque = _Cheque.from_data(data["storage_cheque"])

        return j
