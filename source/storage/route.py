
def storage_functions(function, args):
    """This function routes calls to all of the storage service's
       extra functions
    """
    if function == "open":
        from storage.open import run as _open
        return _open(args)
    else:
        return None

if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(storage_functions))
