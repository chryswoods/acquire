
from Acquire.Identity import IdentityService
from Acquire.Service import Service, set_is_running_service
from Acquire.Crypto import PrivateKey


def test_service_object(aaai_services):
    service = IdentityService(Service(service_type="identity",
                                      service_url="identity"))

    assert(service.uid() is not None)
    assert(service.is_identity_service())
    assert(not service.should_refresh_keys())
    assert(service.is_unlocked())
    assert(not service.is_locked())

    passphrase = PrivateKey.random_passphrase()

    data = service.to_data(passphrase)

    service2 = IdentityService.from_data(data, passphrase)

    assert(service2.uid() == service.uid())
    assert(service2.is_unlocked())
    assert(not service2.is_locked())
    assert(service2.is_identity_service())
    assert(service.canonical_url() == service2.canonical_url())
    assert(not service2.should_refresh_keys())

    keys = service.dump_keys()

    keys = service.load_keys(keys)

    assert(keys[service.private_key().fingerprint()] == service.private_key())
    assert(keys[service.private_certificate().fingerprint()] ==
           service.private_certificate())

    service.refresh_keys()

    assert(service.last_key_update() > service2.last_key_update())
    assert(service.last_certificate().public_key()
           == service2.public_certificate())
    assert(service.last_key() == service2.private_key())
