
import os
import sys

from Acquire.Access import FileWriteRequest


def test_expand_files():
    # basedir = os.path.dirname(os.path.abspath(__file__))

    (a, b) = FileWriteRequest.expand_source_and_destination("*", "")

    assert(len(a) == len(b))
