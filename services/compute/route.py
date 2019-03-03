

def compute_functions(function, args):
    """These are all of the additional functions for the compute service"""
    return None

if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(compute_functions))
