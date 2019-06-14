
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
        result["data"] = obj.to_data()
    elif isinstance(obj, FileMeta):
        result["type"] = "FileMeta"
        result["data"] = obj.to_data()
    elif isinstance(obj, list):
        if len(obj) == 0:
            raise PermissionError("The PAR has not resolved to any object!")

        if not isinstance(obj[0], FileMeta):
            raise TypeError("Unable to handle PARs that result to "
                            "lists of type %s : %s" %
                            (obj[0].__class__.__name__, obj))

        from Acquire.ObjectStore import list_to_string
        result["type"] = "FileMetas"
        result["data"] = list_to_string(obj)
    else:
        raise TypeError(
            "Unable to handle PARs that resolve to objects of type "
            "%s : %s" % (obj.__class__.__name__, obj))

    return result
