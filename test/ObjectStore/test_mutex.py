
from Acquire.ObjectStore import Mutex, MutexTimeoutError
from Acquire.Service import get_service_account_bucket, \
    push_is_running_service, pop_is_running_service

import datetime
import pytest
import time


@pytest.fixture(scope="session")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("objstore")
    push_is_running_service()
    bucket = get_service_account_bucket(str(d))
    pop_is_running_service()
    return bucket


def test_mutex(bucket):
    push_is_running_service()

    try:
        m = Mutex("ObjectStore.test_mutex")

        assert(m.is_locked())
        m.unlock()
        assert(not m.is_locked())
        m.lock()
        assert(m.is_locked())
        m.lock()
        assert(m.is_locked())
        m.unlock()
        assert(m.is_locked())
        m.unlock()
        assert(not m.is_locked())

        m2 = Mutex("ObjectStore.test_mutex")
        assert(m2.is_locked())

        with pytest.raises(MutexTimeoutError):
            m.lock(timeout=0.25)

        assert(not m.is_locked())
        assert(m2.is_locked())

        m2.unlock()
        m.lock()

        assert(m.is_locked())
        assert(not m2.is_locked())

        m.lock(lease_time=0.25)

        time.sleep(0.3)

        with pytest.raises(MutexTimeoutError):
            m.assert_not_expired()

        assert(m.expired())

        with pytest.raises(MutexTimeoutError):
            m.unlock()

        assert(not m.is_locked())

        m.lock(lease_time=0.25)

        time.sleep(0.3)

        assert(m.expired())

        m2.lock()

        assert(m2.is_locked())

        m2.unlock()

        assert(not m2.is_locked())

        with pytest.raises(MutexTimeoutError):
            m.fully_unlock()

        assert(not m.is_locked())
    except:
        pop_is_running_service()
        raise

    pop_is_running_service()