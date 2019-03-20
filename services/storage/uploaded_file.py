
from Acquire.Client import PAR
from Acquire.Client import Authorisation

from Acquire.Service import create_return_value


def run(args):
    """Call this function to complete the two-step process to upload
       a file. This function is called once the PAR has been used
       to upload the file. This verifies that the file has been
       uploaded correctly. It then deletes the PAR and receipts
       the payment
    """

    return create_return_value()
