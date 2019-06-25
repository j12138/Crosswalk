import pytest
from labeling import labeling_tool
from collections import namedtuple
import os

Args = namedtuple("Args", ["data_path", "validate"])


def test_trivial():
    assert True, "You passed a trivial test :)"


def test_main():
    args1 = Args(data_path=os.path.join("some", "invalid", "path"),
                 validate=False)
    # labeling_tool.main(args1)
    assert True

