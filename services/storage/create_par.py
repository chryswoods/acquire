
from Acquire.Client import Authorisation, PAR, PublicKey

from Acquire.Storage import PARRegistry


def run(args):
    """Create a new PAR based on the information supplied
       in the passed half-created PAR, and the supplied
       Authorisation. This will return the URL that will
       need to be used by the PAR to access the required
       data. This will be encrypted using the supplied
       PublicKey
    """

    auth = Authorisation.from_data(args["authorisation"])
    par = PAR.from_data(args["par"])
    secret = args["secret"]

    registry = PARRegistry()
    par_uid = registry.register(par=par, authorisation=auth,
                                secret=secret)

    result = {"par_uid": par_uid}

    return result
