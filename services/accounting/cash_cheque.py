
from Acquire.Service import create_return_value, get_service_account_bucket
from Acquire.ObjectStore import string_to_decimal, string_to_datetime, \
    list_to_string, ObjectStore, Mutex, datetime_to_string

from Acquire.Accounting import DebitNote, CreditNote, Account, \
                               Accounts, Ledger, Transaction

from Acquire.Client import Cheque, PaymentError


def run(args):
    """This function is called to handle request to cash cheques. This
       will verify that the cheque is valid and will then create
       the debit/credit note pair for the transation. It will return
       the CreditNote to the caller so they can see that the funds have
       been reserved, and can receipt the transaction once goods/services
       have been delivered.
    """

    status = 0
    message = None

    credit_notes = []

    try:
        cheque = args["cheque"]
    except:
        raise ValueError("You must supply a cheque to be cashed!")

    try:
        cheque = Cheque.from_data(cheque)
    except Exception as e:
        from Acquire.Service import exception_to_string
        raise TypeError(
            "Unable to interpret the cheque.\n\nCAUSE: %s"
                % exception_to_string(e))

    try:
        spend = args["spend"]
    except:
        spend = None

    if spend is not None:
        try:
            spend = string_to_decimal(spend)
        except Exception as e:
            from Acquire.Service import exception_to_string
            raise TypeError(
                "Unable to interpret the spend.\n\nCause: %s"
                    % exception_to_string(e))

    try:
        resource = str(args["resource"])
    except:
        raise ValueError(
            "You must supply a string representing the resource that will "
            "be paid for using this cheque")

    try:
        account_uid = str(args["account_uid"])
    except:
        raise ValueError(
            "You must supply the UID of the account to which the "
            "cheque will be cashed")

    try:
        receipt_by = args["receipt_by"]
    except:
        raise ValueError(
            "You must supply the datetime by which you promise to "
            "receipt this transaction")

    try:
        receipt_by = string_to_datetime(receipt_by)
    except Exception as e:
        from Acquire.Service import exception_to_string
        raise TypeError(
            "Unable to interpret the receipt_by date.\n\nCAUSE: %s" \
                % exception_to_string(e))

    # now read the cheque - this will only succeed if the cheque
    # is valid, has been signed, has been sent from the right
    # service, and was authorised by the user, the cheque
    # has not expired and we are the
    # service which holds the account from which funds are drawn
    info = cheque.read(resource=resource, spend=spend,
                       receipt_by=receipt_by)

    try:
        description = str(args["description"])
    except:
        description = info["resource"]

    # the cheque is valid
    bucket = get_service_account_bucket()

    try:
        debit_account = Account(uid=info["account_uid"], bucket=bucket)
    except Exception as e:
        from Acquire.Service import exception_to_string
        raise PaymentError(
            "Cannot find the account associated with the cheque"
            "\n\nCAUSE: %s" % exception_to_string(e))

    try:
        credit_account = Account(uid=account_uid, bucket=bucket)
    except Exception as e:
        from Acquire.Service import exception_to_string
        raise PaymentError(
            "Cannot find the account to which funds will be creditted:"
            "\n\nCAUSE: %s" % exception_to_string(e))

    user_guid = info["authorisation"].user_guid()

    # validate that this account is in a group that can be authorised
    # by the user (this should eventually go as the ACLs now allow users
    # to authorised payments from many accounts)
    accounts = Accounts(user_guid=user_guid)
    if not accounts.contains(account=debit_account,
                             bucket=bucket):
        raise PermissionError(
            "The user with UID '%s' cannot authorise transactions from "
            "the account '%s' as they do not own this account." %
            (user_uid, str(debit_account)))

    transaction = Transaction(value=info["spend"],
                              description=description)

    # we have enough information to perform the transaction
    # - this is provisional as the service must receipt everything
    transaction_records = Ledger.perform(transactions=transaction,
                                         debit_account=debit_account,
                                         credit_account=credit_account,
                                         authorisation=info["authorisation"],
                                         is_provisional=True,
                                         receipt_by=receipt_by,
                                         bucket=bucket)

    # extract all of the credit notes to return to the user,
    # and also to record so that we can check if they have not
    # been receipted in time...
    credit_notes = []

    for record in transaction_records:
        credit_notes.append(record.credit_note())

    credit_notes = list_to_string(credit_notes)

    receipt_key = "accounting/cashed_cheque/%s" % info["uid"]
    mutex = Mutex(receipt_key, bucket=bucket)

    try:
        receipted = ObjectStore.get_object_from_json(bucket, receipt_key)
    except:
        receipted = None

    if receipted is not None:
        # we have tried to cash this cheque twice!
        mutex.unlock()
        Ledger.refund(transaction_records, bucket=bucket)
    else:
        info = {"status": "needs_receipt",
                "creditnotes": credit_notes}
        ObjectStore.set_object_from_json(bucket, receipt_key, info)
        mutex.unlock()

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    return_value["credit_notes"] = credit_notes

    return return_value
