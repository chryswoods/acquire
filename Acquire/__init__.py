"""
Acquire : (C) Christopher Woods 2018

System that allows users to log into a distributed serverless
function service to run functions. Data from functions is stored
in an intermediary Object Store. The complete system comprises
three services:

(1) Identity Service (Acquire.Identity)
    This manages user accounts and allows users to authenticate

(2) Accounting Service (Acquire.Accounting)
    This
"""

from Acquire.Stubs import lazy_import as _lazy_import

Access = _lazy_import.lazy_module("Acquire.Access")
Accounting = _lazy_import.lazy_module("Acquire.Accounting")
Crypto = _lazy_import.lazy_module("Acquire.Crypto")
Identity = _lazy_import.lazy_module("Acquire.Identity")
ObjectStore = _lazy_import.lazy_module("Acquire.ObjectStore")
Service = _lazy_import.lazy_module("Acquire.Service")
Client = _lazy_import.lazy_module("Acquire.Client")

__all__ = ["Access", "Accounting", "Client", "Crypto",
           "Identity", "ObjectStore", "Service"]
