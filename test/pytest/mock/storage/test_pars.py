
import pytest

from Acquire.Service import call_function
from Acquire.ObjectStore import PAR


def test_create_par(aaai_services):

    args = {}
    args["user_uid"] = "123"
    args["object_name"] = "test"
    args["md5sum"] = "testsum"

    result = call_function("storage", "open", args=args)

    assert("par" in result)

    par = PAR.from_data(result["par"])

    value = par.read().get_string_object()

    newval = "HERE IS A NEW VALUE € ∆^∂ ∆"

    par.write().set_string_object(newval)

    val = par.read().get_string_object()

    assert(val != value)
    assert(val == newval)
