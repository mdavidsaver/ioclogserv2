#!/usr/bin/env python
"""A testing tool
"""

import sys, socket

host,_,port = sys.argv[1].partition(':')
port = int(port or '7004')

S = socket.create_connection((host,port))

msg = 'This is log message number %d!\n'
N = 0
try:
    while True:
        S.sendall(msg%N)
        N+=1
        if N%100==0:
            print N
finally:
    S.close()
