
from Acquire.Service import get_service_account_bucket
from Acquire.Service import create_return_value

from Acquire.Accounting import Account, Accounts, Transaction, Ledger

from Acquire.Identity import Authorisation


class TransactionError(Exception):
    pass


def run(args):
    """This function is called to handle requests to perform transactions
       between accounts

       Args:
            args (dict): data for account transfers

        Returns:
            dict: contains status, status message and transaction
            records if any are available
    """

    status = 0
    message = None

    transaction_records = None

    try:
        debit_account_uid = str(args["debit_account_uid"])
    except:
        debit_account_uid = None

    try:
        credit_account_uid = str(args["credit_account_uid"])
    except:
        credit_account_uid = None

    try:
        authorisation = Authorisation.from_data(args["authorisation"])
    except:
        authorisation = None

    try:
        transaction = Transaction.from_data(args["transaction"])
    except:
        transaction = None

    try:
        is_provisional = bool(args["is_provisional"])
    except:
        is_provisional = None

    if debit_account_uid is None:
        raise TransactionError("You must supply the account UID "
                               "for the debit account")

    if credit_account_uid is None:
        raise TransactionError("You must supply the account UID "
                               "for the credit account")

    if debit_account_uid == credit_account_uid:
        raise TransactionError(
            "You cannot perform a transaction where the debit and credit "
            "accounts are the same!")

    if transaction is None or transaction.is_null():
        raise TransactionError("You must supply a valid transaction to "
                               "perform!")

    if is_provisional is None:
        raise TransactionError("You must say whether or not the "
                               "transaction is provisional using "
                               "is_provisional")

    if authorisation is None:
        raise PermissionError("You must supply a valid authorisation "
                              "to perform transactions between accounts")

    authorisation.verify(resource=debit_account_uid)
    user_guid = authorisation.user_guid()

    # load the account from which the transaction will be performed
    bucket = get_service_account_bucket()
    debit_account = Account(uid=debit_account_uid, bucket=bucket)

    # validate that this account is in a group that can be authorised
    # by the user - This should eventually go as this is all
    # handled by the ACLs
    if not Accounts(user_guid).contains(account=debit_account,
                                        bucket=bucket):
        raise PermissionError(
            "The user with GUID '%s' cannot authorise transactions from "
            "the account '%s' as they do not own this account." %
            (user_guid, str(debit_account)))

    # now load the two accounts involved in the transaction
    credit_account = Account(uid=credit_account_uid, bucket=bucket)

    # we have enough information to perform the transaction
    transaction_records = Ledger.perform(transactions=transaction,
                                         debit_account=debit_account,
                                         credit_account=credit_account,
                                         authorisation=authorisation,
                                         is_provisional=is_provisional,
                                         bucket=bucket)

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    if transaction_records:
        try:
            transaction_records[0]
        except:
            transaction_records = [transaction_records]

        for i in range(0, len(transaction_records)):
            transaction_records[i] = transaction_records[i].to_data()

        return_value["transaction_records"] = transaction_records

    return return_value
