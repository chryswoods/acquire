
def access_functions(function, args):
    """ This function routes the passed arguments to the function
        selected by the function parameter.
        
        Args:
            function (str) : the function we want to run
            args : arguments to be passed to these functions


        Returns:
            function : selected function with args passed

    """

    if function == "request":
        from access.request import run as _request
        return _request(args)
    elif function == "run_calculation":
        from access.run_calculation import run as _run_calculation
        return _run_calculation(args)
    else:
        from admin.handler import MissingFunctionError
        raise MissingFunctionError()


if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(access_functions))
