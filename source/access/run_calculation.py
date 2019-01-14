
from Acquire.Service import create_return_value
from Acquire.Service import login_to_service_account
from Acquire.Service import call_function

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes

from Acquire.Identity import Authorisation, AuthorisationError

from Acquire.Access import Request, RunRequest


class RequestError(Exception):
    pass


def run(args):
    """This function is used to handle requests to access resources"""

    status = 0
    message = None

    request = None
    authorisation = None

    if "request" in args:
        request = Request.from_data(args["request"])

    if "authorisation" in args:
        authorisation = Authorisation.from_data(args["authorisation"])

    if request is None:
        status = 0
        message = "No request"
        return create_return_value(status, message)

    if authorisation is None:
        raise AuthorisationError(
            "You must provide a valid authorisation to make the request %s"
            % str(request))

    if not isinstance(request, RunRequest):
        raise TypeError(
            "You must pass in a valid RunRequest to request a calculation "
            "is run. The passed request is the wrong type: %s" % str(request))

    # verify that the user has authorised this request
    authorisation.verify(request.signature())

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
