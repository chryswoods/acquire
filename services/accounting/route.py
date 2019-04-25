

def accounting_functions(function, args):
    """This function routes calls to all of the accounting service's
       extra functions

       Args:
            function (str): for selection of function to call
            args: arguments to be passed to the selected function

        Returns:
            function: If valid function selected, function with args passed
            else None
    """
    if function == "cash_cheque":
        from accounting.cash_cheque import run as _cash_cheque
        return _cash_cheque(args)
    elif function == "create_account":
        from accounting.create_account import run as _create_account
        return _create_account(args)
    elif function == "deposit":
        from accounting.deposit import run as _deposit
        return _deposit(args)
    elif function == "get_account_uids":
        from accounting.get_account_uids import run as _get_account_uids
        return _get_account_uids(args)
    elif function == "get_info":
        from accounting.get_info import run as _get_info
        return _get_info(args)
    elif function == "perform":
        from accounting.perform import run as _perform
        return _perform(args)
    else:
        from admin.handler import MissingFunctionError
        raise MissingFunctionError()


if __name__ == "__main__":
    import fdk
    from admin.handler import create_async_handler
    fdk.handle(create_async_handler(accounting_functions))
