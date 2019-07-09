

def compute_functions(function, args):
    """These are all of the additional functions for the compute service"""
    if function == "submit_job":
        from compute.submit_job import run as _submit_job
        return _submit_job(args)
    else:
        from admin.handler import MissingFunctionError
        raise MissingFunctionError()


if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(compute_functions))
