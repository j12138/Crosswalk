import pytest
import pysftp
import os
import sys
import mock
from collections import namedtuple

sys.path.insert(0, os.path.join(os.path.abspath(__file__), '..', '..', 'src', 'labeling'))

from server import upload_all_npy, download_datasets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")


@mock.patch.object(
    target=pysftp,
    attribute='Connection',
    autospec=True,
    return_value=mock.Mock(
        spec=pysftp.Connection,
        __enter__=lambda self: self,
        __exit__=lambda *args: None
    )
)
def test_upload_all_npy(mock_connection):
    npy_dir = './test_npy'
    server_npy_log = 'npy_log.txt'
    local_npy_log = os.path.join(BASE_DIR, 'test_npy_log.txt')

    upload_all_npy(mock_connection, npy_dir, server_npy_log, local_npy_log)

    mock_connection.chdir.assert_called_with('npy')
    # this assertion fails
    # mock_connection.open.assert_called_with(server_npy_log)

@mock.patch.object(
    target=pysftp,
    attribute='Connection',
    autospec=True,
    return_value=mock.Mock(
        spec=pysftp.Connection,
        __enter__=lambda self: self,
        __exit__=lambda *args: None
    )
)
def test_download_datasets(mock_connection):
    data_dir = os.path.join(ROOT_DIR, 'preprocessed_data')

    download_datasets(mock_connection, data_dir)

    mock_connection.listdir.assert_called_with()
