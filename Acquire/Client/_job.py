
__all__ = ["Job"]


class Job:
    """This class provides a handle to represent a compute job
       submitted to the system. It simplifies the process of
       talking to the necessary services, as well as providing
       a handle for the user to control the job after submission
    """
    def __init__(self):
        self._uid = None
        self._status = None

    def is_null(self):
        return self._status is None

    @staticmethod
    def submit(input, resources, account, user=None,
               max_spend=None, max_runtime=None,
               access_service=None):
        """Submit a job to the system. The job will use the passed

           1. input location for all input files as 'input',
           2. the specified resources in 'resources' (includes type of
              machine to run the job plus any software or container
              information)
           3. The financial account to use to pay for the job
           4. Optionally the user that will run the job - if this is not
              passed then the user who owns the account is used
           5. Optionally the maximum spend for the job - if this is not
              passed then the cost will be worked out and must be less
              than the account spend limit
           6. Optionally the maximum runtime of the job - if this is not
              passed then the maximum runtime will be worked out
           7. Optionally pass in the access service to coordinate
              running the job. If this is not passed then the default
              access service for the user will be used
        """
        from Acquire.Access import RunRequest as _RunRequest
        from Acquire.Client import Account as _Account
        from Acquire.Client import User as _User
        from Acquire.Client import PAR as _PAR
        from Acquire.Client import Resources as _Resources
        from Acquire.Client import Location as _Location
        from Acquire.Client import ACLRule as _ACLRule
        from Acquire.Service import Service as _Service

        job = Job()

        if not isinstance(input, _Location):
            raise TypeError("The input location must be type Location")

        if input.is_null():
            raise PermissionError("You cannot submit a null input job!")

        if not isinstance(resources, _Resources):
            raise TypeError("The job resources must be type Resources")

        if not isinstance(account, _Account):
            raise TypeError("The account must be type Account")

        if user is None:
            user = account.user()

        if not isinstance(user, _User):
            raise TypeError("The user must be type User")

        if access_service is None:
            access_service = user.access_service()

        if not issubclass(access_service, _Service):
            raise TypeError("The access_service must be derived from Service")

        if not access_service.is_access_service():
            raise TypeError("The access_service must be an Access Service")

        # First create a PAR so that the access service (and then other
        # services) can read the input for this job
        input_par = _PAR(location=input, user=user, aclrule=_ACLRule.reader())

        # TODO - encode par secret!

        request = _RunRequest(input_par=input_par, resources=resources)

        if max_spend is None or max_runtime is None:
            args = {"request": request.to_data(),
                    "max_spend": str(max_spend),
                    "max_duration": str(max_runtime)}

            result = access_service.call_function(
                                function="instrument_resources", args=args)

            request = _RunRequest.from_data(result["request"])

        job._request = request

        cheque = account.write_cheque(recipient=access_service,
                                      resource=request.fingerprint(),
                                      max_spend=request.max_spend(),
                                      expiry_date=request.max_end_date())

        job._cheque = cheque

        authorisation = user.authorise(request.fingerprint())

        args = {"request": request.to_data(),
                "authorisation": authorisation.to_data(),
                "cheque": cheque.to_data()}

        result = access_service.call_function(function="run_calculation",
                                              args=args)

        job._uid = result["uid"]
        job._status = result["status"]

        return job
