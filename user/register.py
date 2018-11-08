

from Acquire import User

import sys

user = User(sys.argv[1])

(uri,qrcode) = user.create_account(sys.argv[2])

print(uri)
print(qrcode)

