
import asyncio
import fdk
import json
import sys
import os
import subprocess

__all__ = ["create_handler", "create_async_handler",
           "MissingFunctionError"]


class MissingFunctionError(Exception):
    pass


def _one_hot_spare():
    """This function will (in the background) cause the function service
       to spin up another hot spare ready to process another request.
       This ensures that, if a user makes a request while this
       thread is busy, then the cold-start time to spin up another
       thread has been mitigated.

       Args:
            None
        Returns:
            None

       """
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

       Args:
        function (str): select the function to call
        args: arguments to be passed to the function
        additional_functions (function, optional): another function used to
        process the function and arguments

        Returns:
            function : selected function

    """
    if function is None:
        from admin.root import run as _root
        return _root(args)
    elif function == "admin/dump_keys":
        from admin.dump_keys import run as _dump_keys
        return _dump_keys(args)
    elif function == "admin/request_login":
        from admin.request_login import run as _request_login
        return _request_login(args)
    elif function == "admin/get_session_info":
        from admin.get_session_info import run as _get_session_info
        return _get_session_info(args)
    elif function == "admin/login":
        from admin.login import run as _login
        return _login(args)
    elif function == "admin/logout":
        from admin.logout import run as _logout
        return _logout(args)
    elif function == "admin/refresh_keys":
        from admin.refresh_keys import run as _refresh_keys
        return _refresh_keys(args)
    elif function == "admin/request_login":
        from admin.request_login import run as _request_login
        return _request_login(args)
    elif function == "admin/reset":
        from admin.reset import run as _reset
        return _reset(args)
    elif function == "admin/setup":
        from admin.setup import run as _setup
        return _setup(args)
    elif function == "admin/trust_accounting_service":
        from admin.trust_accounting_service import run as \
            _trust_accounting_service
        return _trust_accounting_service(args)
    elif function == "admin/trust_service":
        from admin.trust_service import run as _trust_service
        return _trust_service(args)
    elif function == "admin/test":
        from admin.test import run as _test
        return _test(args)
    elif function == "admin/warm":
        from admin.warm import run as _warm
        return _warm(args)
    else:
        if additional_functions is not None:
            try:
                return additional_functions(function, args)
            except MissingFunctionError:
                pass

        if function.startswith("admin/"):
            raise LookupError("No function called '%s'" % function)

        return _route_function("admin/%s" % function, args)


def _handle(function=None, additional_functions=None, args={}):
    """This function routes calls to sub-functions, thereby allowing
       a single identity function to stay hot for longer. If you want
       to add additional functions then add them via the
       'additional_functions' argument. This should accept 'function'
       and 'args', returning some output if the function is found,
       or 'None' if the function is not available

       Args:
        additional_functions (function, optional): function to route
        args (dict): arguments to be routed with function\
        Returns:
            function: the routed function
       """

    from Acquire.Service import start_profile, end_profile

    pr = start_profile()

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
       or 'None' if the function is not available

       Args:
        additional_functions (function): function to be routed
        ctx: currently unused
        data (str): to be passed as arguments to other functions
        TODO - expand this
        loop: currently unused

        Returns:
            dict: JSON serialisable dict

       """

    # Make sure we set the flag to say that this code is running
    # as part of a service
    from Acquire.Service import push_is_running_service, \
        pop_is_running_service, unpack_arguments, \
        get_service_private_key, pack_return_value, \
        create_return_value

    push_is_running_service()

    result = None

    try:
        (function, args, keys) = unpack_arguments(data,
                                                  get_service_private_key)
    except Exception as e:
        function = None
        args = None
        result = e
        keys = None

    if result is None:
        try:
            result = _handle(function=function,
                             additional_functions=additional_functions,
                             args=args)
        except Exception as e:
            result = e

    result = create_return_value(payload=result)

    try:
        result = pack_return_value(payload=result, key=keys)
    except Exception as e:
        result = pack_return_value(payload=create_return_value(e))

    pop_is_running_service()
    return result


def create_async_handler(additional_functions=None):
    """Function that creates the async handler functions for all standard
        functions, plus the passed additional_functions

        Args:
            additional_functions (optional): other function for which to
            create an async handler

        Returns:
            function: an async instance of the _base_handler function

    """
    async def async_handler(ctx, data=None, loop=None):
        return _base_handler(additional_functions=additional_functions,
                             ctx=ctx, data=data, loop=loop)

    return async_handler


def create_handler(additional_functions=None):
    def handler(ctx=None, data=None, loop=None):
        """Function that creates the handler functions for all standard functions,
       plus the passed additional_functions

       Args:
            additional_functions (optional): other function for which to
            create a handler

        Returns:
            function: A handler function
        """
        return _base_handler(additional_functions=additional_functions,
                             ctx=ctx, data=data, loop=loop)

    return handler
