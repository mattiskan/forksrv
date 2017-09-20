import pytest
import os
import mock
import subprocess
import sys
import time

from forksrv.forksrv import client, server


@pytest.fixture
def tmpfile(tmpdir_factory):
    return tmpdir_factory.mktemp('namespace').join('socketfile.socket').strpath

@pytest.fixture
def one_iteration():
    with mock.patch('forksrv.forksrv.itertools.count', return_value=[1]):
        yield


def test_hello_world_server(tmpfile, one_iteration):
    
    def target_fn():
        subprocess.run('echo hello world'.split())

    pid = os.fork()
    if pid == 0:
        rstdout, wstdout = os.pipe()

        with os.fdopen(wstdout) as sys.stdout:
            client(socketfile=tmpfile)

        assert os.fdopen(rstdout).read().strip() == 'hello world'
        os._exit(1)
        assert False
    else:
        server(target_fn, socketfile=tmpfile)
