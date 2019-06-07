

def identity_functions(function, args):
    """This function routes calls to sub-functions, thereby allowing
       a single identity function to stay hot for longer

       Args:
            function (str): for selection of function to call
            args: arguments to be passed to the selected function

       Returns:
            function: If valid function selected, function with args passed
            else None
    
       """
    if function == "get_session_info":
        from admin.get_session_info import run as _get_session_info
        return _get_session_info(args)
    elif function == "login":
        from admin.login import run as _login
        return _login(args)
    elif function == "logout":
        from admin.logout import run as _logout
        return _logout(args)
    elif function == "register":
        from admin.register import run as _register
        return _register(args)
    elif function == "request_login":
        from admin.request_login import run as _request_login
        return _request_login(args)
    else:
        from admin.handler import MissingFunctionError
        raise MissingFunctionError()


if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(identity_functions))
