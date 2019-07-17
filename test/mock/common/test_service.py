
import pytest

from Acquire.Identity import Authorisation
from Acquire.Crypto import PrivateKey, get_private_key
from Acquire.Service import call_function, Service, get_this_service, \
                push_testing_objstore, pop_testing_objstore, \
                push_is_running_service, pop_is_running_service


@pytest.mark.parametrize("service_url",
                         [("registry"),
                          ("identity"),
                          ("storage"),
                          ("access"),
                          ("compute")])
def test_service(service_url, aaai_services):
    # get the public service from the default API frontend
    privkey = get_private_key("testing")
    response = call_function(service_url, response_key=privkey)
    service = Service.from_data(response["service_info"])

    # also read the service from the object store directly
    push_testing_objstore(aaai_services["_services"][service_url])
    push_is_running_service()
    private_service = get_this_service(need_private_access=True)
    pop_is_running_service()
    pop_testing_objstore()

    # create some test data that contain unicode characters for
    # testing encryption, signing and both encryption and signing
    data = {"hello": "'å∫ç∂ƒ©˙˚'", "key": privkey.public_key().to_data()}

    encrypted = service.encrypt_data(data)
    decrypted = private_service.decrypt_data(encrypted)

    assert(data == decrypted)

    signed = private_service.sign_data(data)
    verified = service.verify_data(signed)

    assert(data == verified)

    enc_sign = service.encrypt_data(private_service.sign_data(data))
    dec_ver = service.verify_data(private_service.decrypt_data(enc_sign))

    assert(data == dec_ver)

    service.call_function("admin/test")

    admin_user = aaai_services[service_url]["user"]
    auth = Authorisation(user=admin_user,
                         resource="dump_keys %s" % service.uid())

    service.call_function(
        function="dump_keys", args={"authorisation": auth.to_data()})
