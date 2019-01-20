
import asyncio
import fdk
import json
import sys
import os
import subprocess

from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile

__all__ = ["create_handler", "create_async_handler"]


def _one_hot_spare():
    """This function will (in the background) cause the function service
       to spin up another hot spare ready to process another request.
       This ensures that, if a user makes a request while this
       thread is busy, then the cold-start time to spin up another
       thread has been mitigated."""
    devnull = open(os.devnull, "w")
    subprocess.Popen(["nohup", sys.executable, "one_hot_spare.py"],
                     stdout=devnull,
                     stderr=subprocess.STDOUT)


def _route_function(function, args, additional_functions=None):
    """Internal function that correctly routes the named function
       to the actual code to run (passing in 'args' as arguments).
       If 'additional_functions' is supplied then this will also
       pass the function through 'additional_functions' to find a
       match
    """
    if function is None:
        from admin.root import run as _root
        result = _root(args)
    elif function == "admin/request_login":
        from admin.request_login import run as _request_login
        result = _request_login(args)
    elif function == "admin/get_keys":
        from admin.get_keys import run as _get_keys
        result = _get_keys(args)
    elif function == "admin/get_status":
        from admin.get_status import run as _get_status
        result = _get_status(args)
    elif function == "admin/login":
        from admin.login import run as _login
        result = _login(args)
    elif function == "admin/logout":
        from admin.logout import run as _logout
        result = _logout(args)
    elif function == "admin/request_login":
        from admin.request_login import run as _request_login
        result = _request_login(args)
    elif function == "admin/setup":
        from admin.setup import run as _setup
        result = _setup(args)
    elif function == "admin/trust_service":
        from admin.trust_service import run as _trust_service
        result = _trust_service(args)
    elif function == "admin/whois":
        from admin.whois import run as _whois
        result = _whois(args)
    elif function == "admin/test":
        from admin.test import run as _test
        result = _test(args)
    elif function == "admin/warm":
        from admin.warm import run as _warm
        result = _warm(args)
    else:
        if additional_functions is not None:
            result = additional_functions(function, args)
        else:
            result = None

        if result is None:
            if function.startswith("admin/"):
                result = {"status": -1,
                          "message": "Unknown function '%s'" % function}
            else:
                return _route_function("admin/%s" % function, args)

    return result


def _base_handler(additional_functions=None, ctx=None, data=None, loop=None):
    """This function routes calls to sub-functions, thereby allowing
       a single identity function to stay hot for longer. If you want
       to add additional functions then add them via the
       'additional_functions' argument. This should accept 'function'
       and 'args', returning some output if the function is found,
       or 'None' if the function is not available"""

    try:
        pr = start_profile()
    except:
        pass

    try:
        args = unpack_arguments(data, get_service_private_key)
    except Exception as e:
        result = {"status": -1,
                  "message": "Cannot unpack arguments (%s): %s"
                  % (data, str(e))}
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
        result = _route_function(function, args, additional_functions)
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


def create_async_handler(additional_functions=None):
    """Function that creates the handler functions for all standard functions,
       plus the passed additional_functions
    """
    async def async_handler(ctx, data=None, loop=None):
        return _base_handler(additional_functions=additional_functions,
                             ctx=ctx, data=data, loop=loop)

    return async_handler


def create_handler(additional_functions=None):
    def handler(ctx, data=None, loop=None):
        return _base_handler(additional_functions=additional_functions,
                             ctx=ctx, data=data, loop=loop)

    return handler
