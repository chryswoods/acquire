
from Acquire.Identity import IdentityService
from Acquire.Service import Service, push_is_running_service, \
       pop_is_running_service, push_testing_objstore, \
       pop_testing_objstore
from Acquire.Crypto import PrivateKey


def test_service_object(tmpdir_factory):
    bucket = tmpdir_factory.mktemp("test_service")
    push_testing_objstore(bucket)
    push_is_running_service()

    try:
        service = Service.create(service_type="identity",
                                 service_url="identity")

        assert(service.uid() is not None)
        assert(service.uid().startswith("STAGE1"))

        service.create_stage2(service_uid="Z9-Z8", response=service.uid())

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

        assert(keys[service.private_key().fingerprint()] ==
               service.private_key())
        assert(keys[service.private_certificate().fingerprint()] ==
               service.private_certificate())

        service.refresh_keys()

        assert(service.last_key_update() > service2.last_key_update())
        assert(service.last_certificate().public_key() ==
               service2.public_certificate())
        assert(service.last_key() == service2.private_key())
    except:
        pop_is_running_service()
        pop_testing_objstore()
        raise

    pop_is_running_service()
    pop_testing_objstore()
