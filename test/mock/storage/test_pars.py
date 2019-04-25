
import pytest

from Acquire.Service import call_function
from Acquire.Client import PAR
from Acquire.Crypto import get_private_key


def test_create_par(aaai_services):

    privkey = get_private_key()
    pubkey = privkey.public_key()

    args = {}
    args["user_uid"] = "123"
    args["object_name"] = "test"
    args["md5sum"] = "testsum"
    args["encrypt_key"] = pubkey.to_data()

    result = call_function("storage", "open", args=args)

    assert("par" in result)

    par = PAR.from_data(result["par"])

    value = par.read(privkey).get_string_object()

    newval = "HERE IS A NEW VALUE € ∆^∂ ∆"

    par.write(privkey).set_string_object(newval)

    val = par.read(privkey).get_string_object()

    assert(val != value)
    assert(val == newval)

    par.close(privkey)

    assert(par.is_null())
