
from Acquire.ObjectStore import Function

import pytest


def _test_sum(a, b):
    return a + b


def test_function():

    f = Function(_test_sum)

    assert(f(a=1, b=3), 4)

    data = f.to_data()

    g = Function.from_data(data)

    assert(g(a=1, b=3), 4)

    f = Function(_test_sum, b=10)

    assert(f(a=1) == 11)

    data = f.to_data()

    g = Function.from_data(data)

    assert(g(a=1), 11)

    f = Function(_test_sum, a=19, b=21)

    assert(f() == 40)

    data = f.to_data()

    g = Function.from_data(data)

    assert(g(), 40)

    assert(g(a=1) == 22)
    assert(g(b=1) == 20)
    assert(g(a=1, b=4) == 5)
