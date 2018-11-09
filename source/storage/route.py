
import asyncio
import fdk
import json

from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile


async def handler(ctx, data=None, loop=None):
    """This function routes calls to sub-functions, thereby allowing
       a single access function to stay hot for longer"""
    try:
        pr = start_profile()
    except:
        pass

    try:
        args = unpack_arguments(data, get_service_private_key)
    except Exception as e:
        result = {"status": -1,
                  "message": "Cannot unpack arguments: %s" % e}
        return json.dumps(result)
    except:
        result = {"status": -1,
                  "message": "Cannot unpack arguments: Unknown error!"}
        return json.dumps(result)

    try:
        function = str(args["function"])
    except:
        function = None

    try:
        if function is None:
            from root import run as _root
            result = _root(args)
        elif function == "setup":
            from setup import run as _setup
            result = _setup(args)
        else:
            result = {"status": -1,
                      "message": "Unknown function '%s'" % function}

    except Exception as e:
        result = {"status": -1,
                  "message": "Error %s: %s" % (e.__class__, str(e))}

    try:
        end_profile(pr, result)
    except:
        pass

    try:
        return pack_return_value(result, args)
    except Exception as e:
        message = {"status": -1,
                   "message": "Error packing results: %s" % e}
        return json.dumps(message)
    except:
        message = {"status": -1,
                   "message": "Error packing results: Unknown error"}
        return json.dumps(message)


if __name__ == "__main__":
    fdk.handle(handler)
