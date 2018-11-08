
from Acquire.Service import login_to_service_account
from Acquire.Service import create_return_value

from Acquire.Accounting import Accounts

from Acquire.Identity import Authorisation


class AccountError(Exception):
    pass


def run(args):
    """This function is called to handle requests for information about
       particular accounts
    """

    status = 0
    message = None

    account = None
    balance_status = None

    try:
        account_name = str(args["account_name"])
    except:
        account_name = None

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        authorisation = None

    if account_name is None:
        raise AccountError("You must supply the account_name")

    if authorisation is None:
        raise AccountError("You must supply a valid authorisation")

    # load the account
    bucket = login_to_service_account()
    account = Accounts(authorisation.user_uid()).get_account(account_name,
                                                             bucket=bucket)

    # validate the authorisation for this account
    authorisation.verify(resource=account.uid())

    balance_status = account.balance_status(bucket=bucket)

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if account:
        return_value["description"] = account.description()
        return_value["overdraft_limit"] = str(account.get_overdraft_limit())

    if balance_status:
        for key in balance_status.keys():
            return_value[key] = str(balance_status[key])

    return return_value
