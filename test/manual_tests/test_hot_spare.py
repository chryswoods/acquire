
from io import BytesIO

import pycurl
import json
import sys


def one_hot_spare():
    """Call this function to ensure that there is one hot spare
       copy of route waiting to service the next request
    """
    args = {}
    args["function"] = None

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
    nrepeats = int(sys.argv[1])
except:
    nrepeats = 1

for i in range(0,nrepeats):
    print("Repeat %d" % (i+1))
    one_hot_spare()
    print("DONE!")
