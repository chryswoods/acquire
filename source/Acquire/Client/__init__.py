"""
Acquire: (C) Christopher Woods 2018

This module implements all of the classes and functions necessary to build the
client (user-facing) interfaces for Acquire
"""

import lazy_import as _lazy_import

from ._qrcode import *
from ._user import *
from ._account import *
from ._wallet import *
from ._errors import *
from ._cheque import *
from ._service import *

# The below objects are useful for the client, so are pulled into
# this module to discourage people using the other Acquire modules
# directly...
PublicKey = _lazy_import.lazy_class("Acquire.Crypto.PublicKey")
PrivateKey = _lazy_import.lazy_class("Acquire.Crypto.PrivateKey")
OTP = _lazy_import.lazy_class("Acquire.Crypto.OTP")
PAR = _lazy_import.lazy_class("Acquire.ObjectStore.PAR")
Authorisation = _lazy_import.lazy_class("Acquire.Identity.Authorisation")

try:
    if __IPYTHON__:
        def _set_printer(C):
            """Function to tell ipython to use __str__ if available"""
            get_ipython().display_formatter.formatters['text/plain'].for_type(
                C,
                lambda obj, p, cycle: p.text(str(obj) if not cycle else '...')
                )

        import sys as _sys
        import inspect as _inspect

        _clsmembers = _inspect.getmembers(_sys.modules[__name__],
                                          _inspect.isclass)

        for _clsmember in _clsmembers:
            _set_printer(_clsmember[1])
except:
    pass
