
from Acquire.ObjectStore import get_datetime_now, \
    datetime_to_string, string_to_datetime, \
    date_to_string, string_to_date, \
    time_to_string, string_to_time

import datetime


def test_datetime():
    dt = get_datetime_now()

    assert(dt.tzinfo == datetime.timezone.utc)

    d = dt.date()
    t = dt.timetz()

    sdt = datetime_to_string(dt)
    assert(dt == string_to_datetime(sdt))

    sd = date_to_string(d)
    assert(d == string_to_date(sd))
    assert(d == string_to_date(date_to_string(dt)))

    st = time_to_string(t)
    assert(t == string_to_time(st))
    assert(t == string_to_time(time_to_string(dt)))
