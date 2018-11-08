
from Acquire import User, get_public_certs

import sys

user = User(sys.argv[1])

try:
    request = user.request_login()
    print(request)
except Exception as e:
    print(e)

logged_in = user.wait_for_login(timeout=10)

print( get_public_certs(user.identity_service_url(), 
                        user.username(), user.session_uid() ) )

if not logged_in:
    print("Still not logged in after 10 seconds? Waiting forever!")
    user.wait_for_login()


