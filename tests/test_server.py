import pytest
import pysftp
import os
import sys
import mock
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__) + '/../'))

from src.server import upload_all_npy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")


# Args = namedtuple("Args", ["data_path", "validate"])
# args1 = Args(data_path=os.path.join("some", "invalid", "path"),
#               validate=False)

@mock.patch('pysftp.Connection')
def test_upload_all_npy(mock_connection):
    npy_dir = './test_npy'
    server_npy_log = 'npy_log.txt'
    local_npy_log = os.path.join(BASE_DIR, 'test_npy_log.txt')

    upload_all_npy(mock_connection, npy_dir, server_npy_log, local_npy_log)
    assert True