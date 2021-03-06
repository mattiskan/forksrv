import os
import socket
import subprocess
import sys
import time
import traceback
import signal
import subprocess
import itertools
from contextlib import contextmanager


# works in both python2 and python3, but unfortunately you can't mix python versions..
try:
    from multiprocessing.reduction import sendfds, recvfds
except ImportError:
    import _multiprocessing

    def sendfds(conn, fds):
        for fd in fds:
            _multiprocessing.sendfd(conn.fileno(), fd)
        
    def recvfds(conn, num):
        return [_multiprocessing.recvfd(conn.fileno()) for _ in range(num)]


# putting the python version in the socket name prevents cross-version connect (they deadlock..)
DEFAULT_SOCKETFILE = '{}/python{}_uds_socket'.format(os.environ['HOME'], sys.version_info.major)
ARGV_SPLIT_TOKEN = '%%'

@contextmanager
def reserve_socketfile(socketfile):
    if os.path.exists(socketfile):
        exit("Socket file {} already exists. Is there already a server running?".format(socketfile))
    try:
        yield
    finally:
        try:
            os.unlink(socketfile)
        except:
            pass


def remote_bash():
    subprocess.run(['/bin/bash'])


def server(target_fn, setup_fn=None, socketfile=DEFAULT_SOCKETFILE):
    with reserve_socketfile(socketfile):
        uds = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        uds.bind(socketfile)
        uds.listen(1)

        if setup_fn:
            setup_fn()

        for _ in itertools.count():
            conn, addr = uds.accept()
           
            pid = os.fork()
            if pid == 0:
                try:
                    for remote,local in zip(recvfds(conn, 3), [sys.stdin, sys.stdout, sys.stderr]):
                        os.dup2(remote, local.fileno())

                    argv = conn.recv(123).strip('\x00').split(ARGV_SPLIT_TOKEN)

                    target_fn(argv)
                except:
                    traceback.print_exc() # print exception to redirected (remote) stderr
                finally:
                    os._exit(1)
                    raise RuntimeError('wat')
            else:
                os.waitpid(pid, 0)
                conn.send(b'\x00') # let client know it can stop blocking
        
def client(argv, socketfile=DEFAULT_SOCKETFILE):
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.connect(socketfile)

    sendfds(conn, [sys.stdin.fileno(), sys.stdout.fileno(), sys.stderr.fileno()])
    conn.send(ARGV_SPLIT_TOKEN.join(argv))

    conn.recv(1) # block this process until remote is finished


if __name__ == '__main__':
    # todo: argparse
    if sys.argv[1] == 'server':
        server(remote_bash)
    elif sys.argv[1] == 'client':
        client(sys.argv[2:])
    else:
        print('bad args')
