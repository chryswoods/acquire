
from Acquire.Service import create_return_value

from Acquire.Accounting import Accounts
from Acquire.Identity import Authorisation


class CreateAccountError(Exception):
    pass


def run(args):
    """This function is called to handle creating accounts for users

        Args:
            args (dict): data for creation of account including name etc.

        Returns:
            dict: contains status, status message and details regarding
                the created account
    
    """

    status = 0
    message = None

    account_uid = None

    try:
        account_name = args["account_name"]
    except:
        account_name = None

    try:
        description = args["description"]
    except:
        description = None

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        authorisation = None

    if account_name is None or description is None \
            or authorisation is None:
        raise CreateAccountError("You must supply both an account name "
                                 "and a description to create an account")

    if not isinstance(authorisation, Authorisation):
        raise TypeError("The passed authorisation must be of type "
                        "Authorisation")

    # try to create a 'main' account for this user
    accounts = Accounts(user_guid=authorisation.user_guid())
    account = accounts.create_account(name=account_name,
                                      description=description,
                                      authorisation=authorisation)

    account_uid = account.uid()

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if account_uid:
        return_value["account_uid"] = account_uid

    return return_value
