

def registry_functions(function, args):
    """This function routes calls to sub-functions, thereby allowing
       a single registry function to stay hot for longer
    """
    raise MissingFunctionError()


if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(registry_functions))
