
import pytest

from Acquire.Crypto import PrivateKey
from Acquire.Service import call_function, Service, get_service_info, \
                _push_testing_objstore, _pop_testing_objstore


@pytest.mark.parametrize("service_url",
                         [("identity"),
                          ("storage"),
                          ("access")])
def test_service(service_url, aaai_services):

    # get the public service from the default API frontend
    privkey = PrivateKey()
    response = call_function(service_url, response_key=privkey)
    service = Service.from_data(response["service_info"])

    # also read the service from the object store directly
    _push_testing_objstore(aaai_services["_services"][service_url])
    private_service = get_service_info(need_private_access=True)
    _pop_testing_objstore()

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

    result = service.call_function("admin/test")

    result = service.call_function("admin/failure")

