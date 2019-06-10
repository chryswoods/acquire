
from Acquire.Service import get_this_service

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes, \
    datetime_to_string

from Acquire.Identity import Authorisation, AuthorisationError

from Acquire.Access import Request, RunRequest, JobSheet

from Acquire.Client import Cheque

from Acquire.Accounting import PaymentError


class RequestError(Exception):
    pass


def run(args):
    """This function is used to handle requests to access resources
        Args:
            args (dict): dictionary containing data to check if a calculation
                         can be run
        Returns:
            dict: dictionary containing the PARs describing the job to be run
    """

    request = None
    authorisation = None
    cheque = None

    if "request" in args:
        request = Request.from_data(args["request"])

    if "authorisation" in args:
        authorisation = Authorisation.from_data(args["authorisation"])

    if "cheque" in args:
        cheque = Cheque.from_data(args["cheque"])

    if request is None:
        return

    if authorisation is None:
        raise AuthorisationError(
            "You must provide a valid authorisation to make the request %s"
            % str(request))

    if cheque is None:
        raise AuthorisationError(
            "You must provide a valid cheque to pay for the request %s"
            % str(request))

    if not isinstance(request, RunRequest):
        raise TypeError(
            "You must pass in a valid RunRequest to request a calculation "
            "is run. The passed request is the wrong type: %s" % str(request))

    # create a job sheet to record all stages of the job
    job_sheet = JobSheet(job=request, authorisation=authorisation)
    job_sheet.set_payment(cheque=cheque)

    # now communicate with all of the services to make the actual
    # requests. This returns the PARs that must be given back to the
    # user to upload the input and trigger the simulation, and the
    # date on which they will expire
    (upload_par, run_par, expires) = job_sheet.request_services()

    # return to the user the PAR used to upload the input data and
    # the PAR on the compute service to call to trigger
    # the start of the calculation
    return {"upload_par": upload_par.to_data(),
            "simulation_par": run_par.to_data(),
            "expiry_date": datetime_to_string(expires),
            "jobsheet_uid": job_sheet.uid()}
