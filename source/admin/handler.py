
import asyncio
import fdk
import json
import sys
import os
import subprocess

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
    elif function == "admin/dump_keys":
        from admin.dump_keys import run as _dump_keys
        result = _dump_keys(args)
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
    elif function == "admin/reset":
        from admin.reset import run as _reset
        result = _reset(args)
    elif function == "admin/setup":
        from admin.setup import run as _setup
        result = _setup(args)
    elif function == "admin/trust_accounting_service":
        from admin.trust_accounting_service import run as \
            _trust_accounting_service
        result = _trust_accounting_service(args)
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
                raise LookupError("No function called '%s'" % function)
            else:
                return _route_function("admin/%s" % function, args)

    return result


def _handle(additional_functions=None, args={}):
    """This function routes calls to sub-functions, thereby allowing
       a single identity function to stay hot for longer. If you want
       to add additional functions then add them via the
       'additional_functions' argument. This should accept 'function'
       and 'args', returning some output if the function is found,
       or 'None' if the function is not available"""

    from Acquire.Service import start_profile, end_profile

    pr = start_profile()

    try:
        function = str(args["function"])
    except:
        function = None

    # if function != "warm":
    #     one_hot_spare()

    result = _route_function(function, args, additional_functions)

    end_profile(pr, result)

    return result


def _base_handler(additional_functions=None, ctx=None, data=None, loop=None):
    """This function routes calls to sub-functions, thereby allowing
       a single function to stay hot for longer. If you want
       to add additional functions then add them via the
       'additional_functions' argument. This should accept 'function'
       and 'args', returning some output if the function is found,
       or 'None' if the function is not available"""

    # make sure we set the flag to say that this code is running
    # as part of a service
    from Acquire.Service import push_is_running_service, \
        pop_is_running_service, unpack_arguments, \
        get_service_private_key, pack_return_value

    push_is_running_service()

    try:
        args = unpack_arguments(data, get_service_private_key)
        is_error = False
    except Exception as e:
        import tblib as _tblib
        tb = _tblib.Traceback(e.__traceback__)
        err_json = {"class": str(e.__class__.__name__),
                    "module": str(e.__class__.__module__),
                    "error": str(e),
                    "traceback": tb.to_dict()}
        result = {"status": -1,
                  "message": "EXCEPTION",
                  "exception": err_json}
        args = {}
        is_error = True

    if not is_error:
        try:
            result = _handle(additional_functions=additional_functions,
                             args=args)
        except Exception as e:
            import tblib as _tblib
            tb = _tblib.Traceback(e.__traceback__)
            err_json = {"class": str(e.__class__.__name__),
                        "module": str(e.__class__.__module__),
                        "error": str(e),
                        "traceback": tb.to_dict()}
            result = {"status": -1,
                      "message": "EXCEPTION",
                      "exception": err_json}

    try:
        result = pack_return_value(result, args)
    except Exception as e:
        message = {"status": -1,
                   "message": "Error packing results: %s" % e}
        result = json.dumps(message)
    except:
        message = {"status": -1,
                   "message": "Error packing results: Unknown error"}
        result = json.dumps(message)

    pop_is_running_service()
    return result


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
