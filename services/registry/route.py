

def registry_functions(function, args):
    """This function routes calls to sub-functions, thereby allowing
       a single registry function to stay hot for longer
    """
    if function == "get_service":
        from registry.get_service import run as _get_service
        return _get_service(args)
    elif function == "register_service":
        from registry.register_service import run as _register_service
        return _register_service(args)
    else:
        from admin.handler import MissingFunctionError
        raise MissingFunctionError()


if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(registry_functions))
