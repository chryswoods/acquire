
import os
import sys

''' Uses OpenSSL to generate cryptographic keys using the username and passphrase
    passed in from the command line
'''

name = sys.argv[1]
passphrase = sys.argv[2]

cmd = "openssl genrsa -out %s.pem -aes128 -passout pass:%s 2048" % (name,passphrase)
os.system(cmd)

cmd = "openssl rsa -pubout -in %s.pem -out %s_public.pem -passin pass:%s" % (name,name,passphrase)
os.system(cmd)

