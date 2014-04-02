# -*- coding: utf-8 -*-

import errno

from twisted.trial import unittest

from ioclogserv.processor import Processor, Destination, Entry
from ioclogserv.util import ConfigDict

from . import testutil


class MockDest(object):
    def __init__(self, ret=False):
        self.C, self.ret = [], ret
        self.S, self.E = 0, 0
    def prepare(self):
        self.S += 1
    def cleanup(self):
        self.E += 1
    def consume(self, E):
        self.C.append(E)
        return self.ret

class TestProc(unittest.TestCase):
    def setUp(self):
        self.P = Processor()
        self.D = [MockDest(), MockDest()]
        self.P.addDest(self.D[0])
        self.P.addDest(self.D[1])

    def test_both(self):
        self.P.proc([(None,None,' test ',1.0)])

        self.assertEqual(len(self.D[0].C), 1)
        self.assertEqual(len(self.D[1].C), 1)

        self.assertIdentical(self.D[0].C[0], self.D[1].C[0])
        self.assertIdentical(self.D[0].C[0].user, None)
        self.assertEqual(self.D[0].C[0].line, 'test')

    def test_stop(self):
        self.D[0].ret = True

        self.P.proc([(None,None,' test ',1.0)])

        self.assertEqual(len(self.D[0].C), 1)
        self.assertEqual(len(self.D[1].C), 0)

_BASIC = """
[processor]
chain = mydest
[mydest]
filename=test.log
"""

_COMPLEX = """
[DEFAULT]
filename = %(name)s.log
[processor]
chain = D1, D2, D3
[D1]
name=all
maxsize=42
numbackup=3
[D2]
name=foobar
users=  foo ,   bar 
stop = true
[D3]
name=experts
"""

class TestProcConf(unittest.TestCase):
    def test_defaults(self):
        P = Processor()

        with open('test.conf', 'w') as F:
            F.write(_BASIC)
        P.load('test.conf')

        self.assertEqual(len(P.dest), 1)
        D = P.dest[0]
        self.assertEqual(D.users, set())
        self.assertEqual(D.filter, False)

    def test_complex(self):
        P = Processor()

        with open('test.conf', 'w') as F:
            F.write(_COMPLEX)
        P.load('test.conf')

        self.assertEqual(len(P.dest), 3)

        D = P.dest[0]
        self.assertEqual(D.users, set())
        self.assertEqual(D.filter, False)

        D = P.dest[1]
        self.assertEqual(D.users, set(['foo','bar']))
        self.assertEqual(D.filter, True)

        D = P.dest[2]
        self.assertEqual(D.users, set())
        self.assertEqual(D.filter, False)

class TestDest(unittest.TestCase, testutil.FileTest):
    def setUp(self):
        from ConfigParser import SafeConfigParser as CP
        import os
        
        try:
            os.remove('mydest.log')
        except OSError as e:
            if e.errno!=errno.ENOENT:
                raise

        P = CP()
        P.add_section('mydest')
        P.set('mydest', 'filename', 'mydest.log')
        P.set('mydest', 'maxsize', '100')
        self.P = P

    def test_pass(self):
        D = Destination(ConfigDict(self.P, 'mydest'))

        E = Entry('test line', None, 1.0)

        D.prepare()
        self.assertFalse(D.consume(E))
        D.cleanup()

        self.assertFileMatch('mydest.log', '.*test line')
