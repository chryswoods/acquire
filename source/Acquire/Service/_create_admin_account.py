
from Acquire.ObjectStore import ObjectStore as _ObjectStore

__all__ = ["create_admin_account"]


def create_admin_account(accounting_service, authorisation):
    """Create the service's financial account on the passed
       accounting service, authorised by the passed authorisation.

       This does nothing if the financial account for this
       service already exists on the passed accounting service
    """
    pass
