
from io import BytesIO

import json

import socket
import sys


def one_hot_spare():
    """Call this function to ensure that there is one hot spare
       copy of route waiting to service the next request
    """
    pass


try:
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    # Create an abstract socket, by prefixing it with null.
    s.bind('\0one_hot_spare_lock')

    one_hot_spare()
except:
    sys.exit(0)
