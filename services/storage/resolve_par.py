
from Acquire.Storage import PARRegistry, DriveMeta, FileMeta


def run(args):
    """Resolve the supplied PAR, returning the authorised Drive
       or File to the user
    """

    par_uid = str(args["par_uid"])
    secret = args["secret"]

    registry = PARRegistry()
    obj = registry.resolve(par_uid=par_uid, secret=secret)

    result = {}

    if isinstance(obj, DriveMeta):
        result["type"] = "DriveMeta"
    elif isinstance(obj, FileMeta):
        result["type"] = "FileMeta"
    else:
        raise TypeError(
            "Unable to handle PARs that resolve to objects of type "
            "%s : %s" % (obj.__class__.__name__, obj))

    result["data"] = obj.to_data()

    return result
