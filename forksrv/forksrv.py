import os
import socket
import subprocess
import sys
import time
import traceback
import signal
from contextlib import contextmanager

from multiprocessing.reduction import recv_handle, send_handle

FILE_SOCKET = f'{os.environ["HOME"]}/uds_socket'

@contextmanager
def noop_context():
    yield

@contextmanager
def reserve_socketfile():
    if os.path.exists(FILE_SOCKET):
        exit(f"Socket file {FILE_SOCKET} already exists. Is there already a server running?")
    try:
        yield
    finally:
        os.unlink(FILE_SOCKET)

def server(server_context=noop_context):
    with reserve_socketfile(), socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as uds:
        uds.bind(FILE_SOCKET)
        uds.listen(1)

        with server_context():
            while True:
                print('Accepting new sessions')

                conn, addr = uds.accept()
                cmd = conn.recv(1024).decode('utf-8')

                print('Starting new session:', cmd)
                stdin, stdout, stderr = recv_handle(conn), recv_handle(conn), recv_handle(conn)
                try:
                    proc = subprocess.Popen(cmd.split(' '), stdin=stdin, stdout=stdout, stderr=stderr)
                    proc.wait()
                except:
                    with open(stderr, 'w') as remote_stderr:
                        traceback.print_exc(file=remote_stderr) # print exception to client
                finally:
                    print('Sending session over')
                    conn.send(b'\x00') # let client know it can stop blocking
        
def client():
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.connect(FILE_SOCKET)

        cmd = ' '.join(sys.argv[2:])

        print('sending cmd:', cmd)
        conn.send(bytes(cmd, 'utf-8'))

        # destination_pid only matters on windows, and we're using unix file sockets, so....
        send_handle(conn, sys.stdin.fileno(), destination_pid=None) 
        send_handle(conn, sys.stdout.fileno(), destination_pid=None)
        send_handle(conn, sys.stderr.fileno(), destination_pid=None)

        conn.recv(1) # block this process until remote is finished

        
if sys.argv[1] == 'server':
    server()
elif sys.argv[1] == 'client':
    client()
else:
    print('bad args')
