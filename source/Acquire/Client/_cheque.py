
import datetime as _datetime
import json as _json

from Acquire.Identity import Authorisation as _Authorisation

from Acquire.ObjectStore import decimal_to_string as _decimal_to_string
from Acquire.ObjectStore import get_datetime_future as _get_datetime_future
from Acquire.ObjectStore import datetime_to_string as _datetime_to_string
from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes
from Acquire.ObjectStore import create_uuid as _create_uuid

from Acquire.Service import get_service_info as _get_service_info

from ._errors import PaymentError


__all__ = ["Cheque"]


class Cheque:
    """This class acts like a real world cheque, except it can only
       be used to transfer money from a regular user to a service
       user's account. This allows users to pay for services. This can be
       written by a user against one of their accounts, to be sent to a
       recipient service to pay for a named service. The recipient can
       send the cheque to the accounting service to trigger payment,
       upon which a CreditNote will be returned. Once receipted,
       payment will be complete.
    """
    def __init__(self):
        self._cheque = None
        self._accounting_service_url = None

    @staticmethod
    def write(account=None, item_signature=None,
              recipient_url=None, max_spend=None,
              expiry_date=None):
        """Create and return a cheque that can be used at any point
           in the future to authorise a transaction. If 'canonical_url'
           is supplied, then only the service with matching canonical
           url can 'cash' the cheque (it will need to sign the cheque
           before sending it to the accounting service). If 'max_spend'
           is specified, then the cheque is only valid up to that
           maximum spend. Otherwise, it is valid up to the maximum
           daily spend limit (or other limits) of the account. If
           'expiry_date' is supplied then this cheque is valid only
           before the supplied datetime. If 'item_signature' is
           supplied then this cheque is only valid to pay for the
           item whose signature is supplied. Note that
           this cheque is for a future transaction, and so no check
           if made if there is sufficient funds now, and this does
           not affect the account. If there are insufficient funds
           when the cheque is cashed (or it breaks spending limits)
           then the cheque will bounce.
        """
        from ._account import Account as _Account

        if not isinstance(account, _Account):
            raise TypeError("You must pass a valid Acquire.Client.Account "
                            "object to write a cheque...")

        if max_spend is not None:
            max_spend = _decimal_to_string(max_spend)

        if expiry_date is not None:
            expiry_date = _datetime_to_string(expiry_date)

        if recipient_url is not None:
            recipient_url = str(recipient_url)

        info = _json.dumps({"recipient_url": recipient_url,
                            "max_spend": max_spend,
                            "expiry_date": expiry_date,
                            "uid": _create_uuid(),
                            "item_signature": str(item_signature),
                            "account_uid": account.uid()})

        auth = _Authorisation(user=account.user(), resource=info)

        data = _json.dumps({"info": info, "authorisation": auth.to_data()})

        cheque = Cheque()

        cheque._cheque = _bytes_to_string(
                            account.accounting_service().encrypt(data))
        cheque._accounting_service_url = \
            account.accounting_service().canonical_url()

        return cheque

    def cash(self, spend, item_signature=None,
             receipt_within=3600):
        """Cash this cheque, specifying how much to be cashed,
           and the signature of the item that will be paid for
           using this cheque. This will send the cheque to the
           accounting service (if we trust that accounting service).
           The accounting service will check that the cheque is valid,
           and the signature of the item is correct. It will then
           withdraw 'spend' funds from the account that signed the
           cheque, returning valid CreditNote(s) that can be trusted
           to show that the funds exist.

           If 'receipt_within' is set, then the CreditNotes will
           be automatically cancelled if they are not
           receipted within 'receipt_within' seconds

           It is your resposibility to receipt the note for
           the actual valid incurred once the service has been
           delivered, thereby actually transferring the cheque
           funds into your account (on that accounting service)

           This returns a list of the CreditNote(s) that were
           cashed from the cheque
        """
        if self._cheque is None:
            raise PaymentError("You cannot cash a null cheque!")

        # sign the cheque to show we have seen it
        service = _get_service_info(need_private_access=True)
        self._cheque = service.sign_data(self._cheque)

        # get the trusted accounting service that will honour the cheque
        accounting_service = self.accounting_service()

        # when do we guarantee to receipt the credit notes by?
        receipt_by = _get_datetime_future(receipt_within)

        # which account should the money be paid into?
        account_uid = service.service_user_account_uid(
                                accounting_service=accounting_service)

        # next - send the cheque to the accounting service to
        # show that we know the item_id and want to cash it
        result = accounting_service.call_function(
            function="cash_cheque",
            args={"cheque": self.to_data(),
                  "spend": _decimal_to_string(spend),
                  "item_signature": item_signature,
                  "account_uid": account_uid,
                  "receipt_by": _datetime_to_string(receipt_by)})

        credit_notes = None

        try:
            from Acquire.Accounting import CreditNote as _CreditNote
            credit_notes = _CreditNote.from_data(result["credit_notes"])
        except Exception as e:
            raise PaymentError(
                "Attempt to cash the cheque has not resulted in a "
                "valid CreditNote? Error = %s" % str(e))

        total_cashed = 0

        for note in credit_notes:
            total_cashed = total_cashed + note.value()
            if note.account_uid() != account_uid:
                raise PaymentError(
                    "The cashed cheque is paying into the wrong account! "
                    "%s. It should be going to %s" %
                    (note.account_uid(), account_uid))

        if total_cashed != spend:
            raise PaymentError(
                "The value of the cheque (%s) does not match the total value "
                "of the credit note(s) returned (%s)" % (spend, total_cashed))

        return credit_notes

    def accounting_service_url(self):
        """Return the URL of the accounting service that will honour
           this cheque
        """
        return self._accounting_service_url

    def accounting_service(self):
        """Return the accounting service that will honour this cheque.
           Note that this will only return the service if it is trusted
           by the service on which this function is called
        """
        service = _get_service_info()
        accounting_service = service.get_trusted_service(
                                            self.accounting_service_url())

        if not accounting_service.is_accounting_service():
            from Acquire.Service import ServiceError
            raise ServiceError(
                "The service that is supposed to honour the cheque (%s) "
                "does not appear to be a valid accounting service" %
                (str(accounting_service)))

        return accounting_service

    def to_data(self):
        """Return a json-serialisable dictionary for this object"""
        data = {}

        if self._cheque is not None:
            data["accounting_service_url"] = self._accounting_service_url
            data["cheque"] = self._cheque

        return data

    @staticmethod
    def from_data(data):
        """Return a cheque constructed from the passed (json-deserialised
           dictionary)"""
        cheque = Cheque()

        if (data and len(data) > 0):
            cheque._cheque = data["cheque"]
            cheque._accounting_service_url = data["accounting_service_url"]

        return cheque
