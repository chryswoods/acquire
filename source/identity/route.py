
import asyncio
import fdk
import json
import sys
import os
import subprocess

from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile


def one_hot_spare():
    """This function will (in the background) cause the function service
       to spin up another hot spare ready to process another request.
       This ensures that, if a user makes a request while this
       thread is busy, then the cold-start time to spin up another
       thread has been mitigated."""
    devnull = open(os.devnull, "w")
    subprocess.Popen(["nohup", sys.executable, "one_hot_spare.py"],
                     stdout=devnull,
                     stderr=subprocess.STDOUT)

def handler(ctx, data=None, loop=None):
    """This function routes calls to sub-functions, thereby allowing
       a single identity function to stay hot for longer"""

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

    # if function != "warm":
    #     one_hot_spare()

    try:
        if function is None:
            from identity.root import run as _root
            result = _root(args)
        elif function == "request_login":
            from identity.request_login import run as _request_login
            result = _request_login(args)
        elif function == "get_keys":
            from identity.get_keys import run as _get_keys
            result = _get_keys(args)
        elif function == "get_status":
            from identity.get_status import run as _get_status
            result = _get_status(args)
        elif function == "login":
            from identity.login import run as _login
            result = _login(args)
        elif function == "logout":
            from identity.logout import run as _logout
            result = _logout(args)
        elif function == "register":
            from identity.register import run as _register
            result = _register(args)
        elif function == "request_login":
            from identity.request_login import run as _request_login
            result = _request_login(args)
        elif function == "setup":
            from identity.setup import run as _setup
            result = _setup(args)
        elif function == "whois":
            from identity.whois import run as _whois
            result = _whois(args)
        elif function == "test":
            from identity.test import run as _test
            result = _test(args)
        elif function == "warm":
            from identity.warm import run as _warm
            result = _warm(args)
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


async def async_handler(ctx, data=None, loop=None):
    return handler(ctx, data, loop)


if __name__ == "__main__":
    fdk.handle(async_handler)
