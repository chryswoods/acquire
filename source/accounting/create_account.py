
from Acquire.Service import get_trusted_service_info
from Acquire.Service import create_return_value

from Acquire.Accounting import Accounts
from Acquire.Identity import Authorisation


class CreateAccountError(Exception):
    pass


def run(args):
    """This function is called to handle creating accounts for users"""

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

    authorisation.verify()

    # try to create a 'main' account for this user
    accounts = Accounts(authorisation.user_uid())
    account = accounts.create_account(name=account_name,
                                      description=description)

    account_uid = account.uid()

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if account_uid:
        return_value["account_uid"] = account_uid

    return return_value
