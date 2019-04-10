
import os

for dirpath, dirnames, filenames in os.walk("accounting"):
    for filename in filenames:
        if not filename.endswith("._data"):
            full = "%s/%s" % (dirpath,filename)
            cmd = "mv %s %s._data" % (full, full)
            print(cmd)
            os.system(cmd)

