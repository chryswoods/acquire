
import fdk

from admin.handler import create_async_handler


def access_functions(function, args):
    """These are all of the additional functions for the access service"""
    if function == "request":
        from access.request import run as _request
        return _request(args)
    elif function == "run_calculation":
        from access.run_calculation import run as _run_calculation
        return _run_calculation(args)
    elif function == "request_bucket":
        from access.request_bucket import run as _request_bucket
        return _request_bucket(args)
    else:
        return None

if __name__ == "__main__":
    fdk.handle(create_async_handler(access_functions))
