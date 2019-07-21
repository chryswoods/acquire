
import pytest

from Acquire.ObjectStore import create_uid, validate_is_uid, \
                                get_datetime_now


def test_create_uid():
    validate_is_uid('2019-06-13T15:40:15.809684/a499a5b6')
    validate_is_uid(
        '2019-06-13T15:40:42.784734/dc396049-ab04-4564-86d0-c78a3f43e22d')
    validate_is_uid('fc22b2fe-db60-4d80-b652-01b08fe36e27')
    validate_is_uid('03a07bcf')

    now = get_datetime_now()

    for _i in range(0, 100):
        assert(create_uid(short_uid=True) != create_uid(short_uid=True))
        assert(create_uid(short_uid=False) != create_uid(short_uid=False))

        validate_is_uid(create_uid())
        validate_is_uid(create_uid(short_uid=True))
        validate_is_uid(create_uid(short_uid=False))
        validate_is_uid(create_uid(short_uid=True, include_date=now))
        validate_is_uid(create_uid(short_uid=False, include_date=now))

    with pytest.raises(TypeError):
        validate_is_uid(None)

    with pytest.raises(TypeError):
        validate_is_uid("ABCDEFGH")
