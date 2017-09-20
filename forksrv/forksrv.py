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

try:
    from multiprocessing.reduction import sendfds, recvfds
except ImportError:
    import _multiprocessing

    def sendfds(conn, fds):
        for fd in fds:
            _multiprocessing.sendfd(conn.fileno(), fd)
        
    def recvfds(conn, num):
        return [_multiprocessing.recvfd(conn.fileno()) for _ in range(num)]



DEFAULT_SOCKETFILE = '{}/uds_socket'.format(os.environ['HOME'])


@contextmanager
def reserve_socketfile(socketfile):
    if os.path.exists(socketfile):
        exit("Socket file {} already exists. Is there already a server running?".format(socketfile))
    try:
        yield
    finally:
        os.unlink(socketfile)


def remote_bash():
    subprocess.run(['/bin/bash'])


def server(target_fn, setup_fn=None, socketfile=DEFAULT_SOCKETFILE):
    with reserve_socketfile(socketfile), socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as uds:
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

                    target_fn()
                except:
                    traceback.print_exc() # print exception to redirected (remote) stderr
                finally:
                    os._exit(1)
                    raise RuntimeError('wat')
            else:
                os.waitpid(pid, 0)
                conn.send(b'\x00') # let client know it can stop blocking
        
def client(socketfile=DEFAULT_SOCKETFILE):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.connect(socketfile)
        sendfds(conn, [sys.stdin.fileno(), sys.stdout.fileno(), sys.stderr.fileno()])
        conn.recv(1) # block this process until remote is finished


if __name__ == '__main__':
    if sys.argv[1] == 'server':
        server(remote_bash)
    elif sys.argv[1] == 'client':
        client()
    else:
        print('bad args')
