
from Acquire.Service import create_return_value
from Acquire.Service import get_service_info

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes

from Acquire.Identity import Authorisation, AuthorisationError

from Acquire.Access import Request, RunRequest

from Acquire.Client import Cheque

from Acquire.Accounting import PaymentError


class RequestError(Exception):
    pass


def run(args):
    """This function is used to handle requests to access resources"""

    status = 0
    message = None

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
        status = 0
        message = "No request"
        return create_return_value(status, message)

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

    # verify that the user has authorised this request
    authorisation.verify(request.signature())

    # now find the cost to run the job - this will be a compute
    # cost and a storage cost
    total_cost = 10

    # create a record for this job
    #record = JobRecord(request=request, total_cost=total_cost,
    #                   payment_account=account_uid)
    #                   # child services = services....

    # send the cheque to the accounting service to get a credit note
    # to show that we will be paid for this job
    try:
        credit_notes = cheque.cash(spend=total_cost,
                                   resource=request.signature())
    except Exception as e:
        raise PaymentError(
            "Problem cashing the cheque used to pay for the calculation: "
            "ERROR = %s" % str(e))

    if credit_notes is None or len(credit_notes) == 0:
        raise PaymentError("Cannot be paid!")

    # save this credit_note so that it is not lost
    # bucket = _get_service_account_bucket()

    # the access service will be paid for the job. We need to now
    # create the Credit/Debit note pairs to transfer funds from
    # the access service to the selected storage and compute services

    # we will then store these in the object store against the credit
    # note - only once everything is receipted to us will we then
    # calculate how much we want to receipt back to the user (we may
    # take a cut or have other overheads)

    # ... check that the user has enough money to perform this calculation
    # ... create a credit note for the storage service and the run service
    # ... that can be used to pay for the compute and data

    # ... choose a storage service which will store the data for the
    # ... simulation. Get the encryption keys for this service so that
    # ... we can safely send it data about how to receipt the storage
    # ... without worrying that anyone can interfere with that data

    # ... choose a run service which will run the simulation. Get the
    # ... encryption keys for this service so that we can safely send
    # ... it data about how to write output and receipt the account

    # 1. ask the storage service to create a new bucket for the simulation
    # 2. create a PAR for the bucket used by the user to upload their
    #    input file (as described in the runinfo in the RunRequest)
    # 3. create a bucket write PAR that will be used by the run service
    # 4. create the data that will be passed (at the end of the calculation)
    #    to the storage service to delete the bucket write PAR and finalise
    #    the bucket. This will include the credit note that will need to be
    #    receipted once the total size of the bucket is known. Encrypt
    #    this data using the storage service encryption key
    # 5. create the data that will passed to the run service to run the
    #    calculation. This will contain the PAR for writing, the credit
    #    note to receipt the calculation, and the encrypted data that
    #    the run service will relay to the storage service. Encrypt
    #    this data using the run service encryption key.
    # 6. Package up the write PAR with the URL and function to call the
    #    run service, with the encrypted run data, so that this can be
    #    sent back to the user. The user should use the PAR to upload
    #    the input data, then call the run function url, passing in the
    #    encrypted data as arguments.

    status = 0
    message = "Request has been validated"

    return_value = create_return_value(status, message)

    return return_value
