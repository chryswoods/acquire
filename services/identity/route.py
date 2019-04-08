

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
    
    if function == "request_login":
        from admin.request_login import run as _request_login
        return _request_login(args)
    elif function == "get_keys":
        from admin.get_keys import run as _get_keys
        return _get_keys(args)
    elif function == "get_status":
        from admin.get_status import run as _get_status
        return _get_status(args)
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
    elif function == "whois":
        from admin.whois import run as _whois
        return _whois(args)
    else:
        return None

if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(identity_functions))
