
from io import BytesIO

import json
import sys


def one_hot_spare():
    """Call this function to ensure that there is one hot spare
       copy of route waiting to service the next request
    """
    pass


try:
    nrepeats = int(sys.argv[1])
except:
    nrepeats = 1

for i in range(0,nrepeats):
    print("Repeat %d" % (i+1))
    one_hot_spare()
    print("DONE!")
