
from io import BytesIO

import pycurl
import json


def one_hot_spare():
    """Call this function to ensure that there is one hot spare
       copy of route waiting to service the next request
    """
    args = {}
    args["function"] = "warm"

    service_url = "http://130.61.60.88:8080/t/storage"

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


one_hot_spare()
