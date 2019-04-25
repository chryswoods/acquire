
from Acquire.Service import call_function
from Acquire.Crypto import PrivateKey
from Acquire.Client import Wallet

registry_uid = "a0-a0"

wallet = Wallet()

try:
    service = wallet.get_service(service_uid=registry_uid)
except Exception as e:
    print(e)
    service = None

if service is None:
    from Acquire.Service import Service as _Service
    from Acquire.Service import call_function as _call_function
    response_key = PrivateKey()
    registry_url = "http://fn.acquire-aaai.com:8080/t/registry"
    data = call_function(registry_url, response_key=response_key)
    service = _Service.from_data(data["service_info"])
    print("WARNING - Insecure method of getting the registry service!")
    print("Please validate that the service keys are correct!")
    print(service)
    print("Public key: %s" % service.public_key().to_data())
    print("Public cert: %s" % service.public_certificate().to_data())
    ok = input("Everything ok? (y/n): ")
    if ok != "y":
        raise PermissionError("Untrusted service!")

print("""
# This file contains the public keys and certs for the 
# registry with UID %s, 
# and canonical_url %s

public_key = %s

public_certificate = %s

""" % (service.uid(), service.canonical_url(),
       service.public_key().to_data(),
       service.public_certificate().to_data()))
