"""
Acquire: (C) Christopher Woods 2018

This module implements all of the classes and functions necessary to build the
client (user-facing) interfaces for Acquire
"""

from ._qrcode import *
from ._user import *
from ._account import *
from ._wallet import *
from ._errors import *
from ._cheque import *
from ._service import *

# The below objects are useful for the client, so are pulled into
# this module to discourage people using the other Acquire modules
# directly... One day I want to lazy-load all of these...
from Acquire.Crypto import PublicKey
from Acquire.Crypto import PrivateKey
from Acquire.Crypto import OTP
from Acquire.ObjectStore import PAR
from Acquire.Identity import Authorisation

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
