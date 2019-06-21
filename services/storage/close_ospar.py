
from Acquire.ObjectStore import ObjectStore

from Acquire.Service import get_service_account_bucket


def run(args):
    """Call this function to close an OSPar"""

    par_uid = str(args["par_uid"])
    url_checksum = args["url_checksum"]

    if url_checksum is None:
        raise PermissionError(
            "You must supply a checksum of the URL of the PAR to prove "
            "that you have permission to issue a close request")

    url_checksum = str(url_checksum)

    if len(url_checksum) == 0:
        raise PermissionError(
            "You must supply a checksum of the URL of the PAR to prove "
            "that you have permission to issue a close request")

    ObjectStore.close_par(par_uid=par_uid, url_checksum=url_checksum)
