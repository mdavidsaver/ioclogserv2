# -*- coding: utf-8 -*-

from twisted.internet import task
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest

from ioclogserv.collector import Collector

class MockEP(object):
    def __init__(self):
        self.reset()
    def reset(self):
        self.A = 0
    def ack(self):
        self.A += 1

class MockProc(object):
    def __init__(self):
        self.reset()
    def reset(self):
        self.R = []
    def proc(self, A):
        self.R.append(A)

class TestColl(unittest.TestCase):

    def setUp(self):
        self.clock = task.Clock()
        self.P, self.EP = MockProc(), MockEP()
        self.C = Collector(self.P)
        self.C.connect(self.EP)
        self.C.reactor = self.clock

    def test_low(self):
        """Don't send enough to trigger a flush
        """
        C, P, N = self.C, self.P, 0

        for N in range(9):
            C.add(N, None, 'line %d'%N, float(N))

        self.assertEqual(len(C.buf), 9)
        self.assertTrue(C.flushing is None)

    @inlineCallbacks
    def test_collect(self):
        """Send exactly enough to trigger a flush
        """
        C, P, N = self.C, self.P, 0
        while not C.flushing:
            N += 1
            C.add(N, None, 'line %d'%N, float(N))

        self.assertTrue(C.flushing is True)

        self.clock.advance(20)        

        self.assertTrue(C.flushing)

        yield C.flushing

        self.assertEqual(self.EP.A, 1)
        self.assertEqual(len(P.R), 1)
        self.assertEqual(len(P.R[0]), 10)

        self.assertEqual(P.R[0][0][0], 1)
        self.assertEqual(P.R[0][-1][0], 10)

        self.assertTrue(C.flushing is None)

    @inlineCallbacks
    def test_excess(self):
        """Send more than enough to trigger a flush, but
        not enough to cause a second flush
        """
        C, P, N = self.C, self.P, 0

        for N in range(15):
            C.add(N, None, 'line %d'%N, float(N))

        self.clock.advance(20)        

        yield C.flushing

        self.assertEqual(self.EP.A, 1)
        self.assertEqual(len(P.R), 1)
        self.assertEqual(len(P.R[0]), 15)

        self.assertEqual(len(C.buf), 0)

        self.assertTrue(C.flushing is None)

    @inlineCallbacks
    def test_2flush(self):
        """Send more than enough to trigger two flushes, but
        not enough to cause an overflow
        """
        C, P, N = self.C, self.P, 0

        for N in range(15):
            C.add(N, None, 'line %d'%N, float(N))

        self.assertEqual(len(C.buf), 15)
        self.clock.advance(20)     
        self.assertEqual(len(C.buf), 0)

        for N in range(16):
            C.add(N, None, 'line %d'%N, float(N))

        self.assertEqual(len(C.buf), 16)
        self.assertEqual(self.EP.A, 0)
        self.assertEqual(len(P.R), 0)

        yield C.flushing

        self.assertEqual(len(C.buf), 16)

        self.assertEqual(self.EP.A, 1)
        self.assertEqual(len(P.R), 1)
        self.assertEqual(len(P.R[0]), 15)

        self.assertTrue(C.flushing is True)

        self.clock.advance(20)     
        self.assertEqual(len(C.buf), 0)

        yield C.flushing

        self.assertTrue(C.flushing is None)

        self.assertEqual(len(C.buf), 0)
        self.assertEqual(self.EP.A, 2)
        self.assertEqual(len(P.R), 2)
        self.assertEqual(len(P.R[1]), 16)

    @inlineCallbacks
    def test_oflow(self):
        """Send more than enough to trigger two flushes, and
        enough to trigger an overflow
        """
        C, P, N = self.C, self.P, 0

        for N in range(15):
            C.add(N, None, 'line %d'%N, float(N))

        self.assertEqual(len(C.buf), 15)
        self.clock.advance(20)     
        self.assertEqual(len(C.buf), 0)

        for N in range(26):
            C.add(N, None, 'line %d'%N, float(N))

        self.assertEqual(len(C.buf), 21)
        self.assertEqual(C.buf[-1][2], 'messages lost')

        yield C.flushing

        self.assertEqual(self.EP.A, 1)
        self.assertEqual(len(P.R), 1)
        self.assertEqual(len(P.R[0]), 15)
        self.assertEqual(len(C.buf), 21)

        self.clock.advance(20)     
        self.assertEqual(len(C.buf), 0)

        yield C.flushing

        self.assertTrue(C.flushing is None)

        self.assertEqual(len(C.buf), 0)
        self.assertEqual(self.EP.A, 2)
        self.assertEqual(len(P.R), 2)
        self.assertEqual(len(P.R[1]), 21)
