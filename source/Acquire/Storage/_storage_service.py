
import uuid as _uuid
from copy import copy as _copy
import os as _os

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import PublicKey as _PublicKey

from Acquire.Service import call_function as _call_function
from Acquire.Service import Service as _Service

from ._errors import StorageServiceError

__all__ = ["StorageService"]


class StorageService(_Service):
    """This is a specialisation of Service for Storage Services"""
    def __init__(self, other=None):
        if isinstance(other, _Service):
            self.__dict__ = _copy(other.__dict__)

            if not self.is_storage_service():
                raise StorageServiceError(
                    "Cannot construct an StorageService from "
                    "a service which is not an storage service!")

            # the storage service must define the ID for the compartment
            # in which user data will be stored
            self._storage_compartment_id = _os.getenv("STORAGE_COMPARTMENT")

            if self._storage_compartment_id is None:
                raise StorageServiceError(
                    "Every storage service must supply the ID of the "
                    "compartment in which user data should be stored. This "
                    "should be provided via the 'STORAGE_COMPARTMENT' "
                    "environment variable")
        else:
            _Service.__init__(self)

    def storage_compartment(self):
        """Return the ID of the compartment in which user data will be
           stored. This should be a different compartment to the one used
           to store management data for the storage service"""
        try:
            return self._storage_compartment_id
        except:
            pass

        raise StorageServiceError(
            "The ID of the compartment for the storage account has not been "
            "set. This should have been set when the StorageService was "
            "constructed.")
