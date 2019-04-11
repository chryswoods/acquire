
from Acquire.Service import get_service_account_bucket
from Acquire.Service import create_return_value

from Acquire.Accounting import Accounts

from Acquire.Identity import Authorisation


class ListAccountsError(Exception):
    pass


def run(args):
    """This function is called to handle requests for the UIDs of accounts"""

    status = 0
    message = None

    account_uids = None

    try:
        account_name = str(args["account_name"])
    except:
        account_name = None

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        authorisation = None

    try:
        user_guid = str(args["user_guid"])
    except:
        user_guid = None

    is_authorised = False

    if authorisation is not None:
        if not isinstance(authorisation, Authorisation):
            raise TypeError("All authorisations must be of type "
                            "Authorisation")

        if user_guid:
            if user_guid == authorisation.user_guid():
                authorisation.verify(resource="get_account_uids")
                is_authorised = True
        else:
            authorisation.verify(resource="get_account_uids")
            user_guid = authorisation.user_guid()
            is_authorised = True

    if user_guid is None:
        raise ValueError("You must supply either an Authorisation or the "
                         "user_guid")

    # try to create a 'main' account for this user
    account_uids = {}
    accounts = Accounts(user_guid=user_guid)

    if account_name is None:
        if not is_authorised:
            raise PermissionError(
                "You cannot list general information about a user's "
                "accounts unless you have authenticated as the user!")

        bucket = get_service_account_bucket()
        account_names = accounts.list_accounts(bucket=bucket)

        for account_name in account_names:
            account = accounts.get_account(account_name, bucket=bucket)
            account_uids[account.uid()] = account.name()

    else:
        if not is_authorised:
            try:
                account = accounts.get_account(account_name)
            except:
                # don't leak any information
                raise ListAccountsError(
                    "No account called '%s' for user '%s'" %
                    (account_name, user_guid))
        else:
            # allow the user to see the real exception if this
            # account doesn't exist
            account = accounts.get_account(account_name)

        account_uids[account.uid()] = account.name()

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if account_uids:
        return_value["account_uids"] = account_uids

    return return_value
