
from io import BytesIO

import pycurl
import json

import socket
import sys


def one_hot_spare():
    """Call this function to ensure that there is one hot spare
       copy of route waiting to service the next request
    """
    args = {}
    args["function"] = "warm"

    service_url = "http://130.61.60.88:8080/t/identity"

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, service_url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.POSTFIELDS, json.dumps(args).encode("utf-8"))

    try:
        c.perform()
        c.close()
    except:
        pass


try:
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    ## Create an abstract socket, by prefixing it with null. 
    s.bind( '\0one_hot_spare_lock') 

    one_hot_spare()
except:
    sys.exit (0) 
