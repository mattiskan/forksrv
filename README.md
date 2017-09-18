# Forksrv
Provides the base for running a cmd in a separate process.

Example Usage:
```
# start server
$ python forksrv/forksrv.py server
```

```
# Run commands in different terminal on same machine
(virtualenv_run) mylaptop:forksrv mattis$ python forksrv/forksrv.py client echo hello
sending cmd: echo hello
hello

(virtualenv_run) mylaptop:forksrv mattis$ python forksrv/forksrv.py client python
sending cmd: python
Python 3.6.2 (default, Jul 17 2017, 16:44:45)
[GCC 4.2.1 Compatible Apple LLVM 8.1.0 (clang-802.0.42)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> exit()
```