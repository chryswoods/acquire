
from Acquire.Service import create_return_value
from Acquire.ObjectStore import string_to_decimal, string_to_datetime, \
    list_to_string

from Acquire.Accounting import DebitNote, CreditNote

from Acquire.Client import Cheque


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
        raise TypeError("Unable to interpret the cheque. Error: %s" % str(e))

    try:
        spend = args["spend"]
    except:
        spend = None

    if spend is not None:
        try:
            spend = string_to_decimal(spend)
        except Exception as e:
            raise TypeError(
                "Unable to interpret the spend. Error: %s" % str(e))

    try:
        item_signature = str(args["item_signature"])
    except:
        item_signature = None

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
        raise TypeError(
            "Unable to interpret the receipt_by date. Error: %s" % str(e))

    # now read the cheque
    cheque_data = cheque.read(item_signature=item_signature)

    print(cheque_data)

    status = 0
    message = "Success"

    return_value = create_return_value(status, message)

    credit_notes = [CreditNote()]

    return_value["credit_notes"] = list_to_string(credit_notes)

    return return_value
