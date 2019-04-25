
from Acquire.Service import get_service_account_bucket

from Acquire.Accounting import Accounts

from Acquire.Identity import Authorisation


class AccountError(Exception):
    pass


def run(args):
    """This function is called to handle requests for information about
       particular accounts

       Args:
            args (dict): data for account query

        Returns:
            dict: contains status, status message and details regarding
                the account including balance (if available), overdraft
                limit and a description of the account
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
    bucket = get_service_account_bucket()
    accounts = Accounts(user_guid=authorisation.user_guid())
    account = accounts.get_account(account_name, bucket=bucket)

    # validate the authorisation for this account
    authorisation.verify(resource="get_info %s" % account.uid())

    balance = account.balance()

    return_value = {}

    return_value["description"] = account.description()
    return_value["overdraft_limit"] = str(account.get_overdraft_limit())
    return_value["balance"] = balance.to_data()

    return return_value
