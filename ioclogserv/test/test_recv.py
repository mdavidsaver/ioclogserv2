# -*- coding: utf-8 -*-

import logging
logging.basicConfig(level=logging.WARN)

from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet import defer, task, address

from ioclogserv.receiver import IOCLogServerFactory

class TCPStringTransport(proto_helpers.StringTransportWithDisconnection):
    def __init__(self):
        proto_helpers.StringTransportWithDisconnection.__init__(self)
        self.KA = None
    def setTcpKeepAlive(self, V):
        self.KA = V

class MockColl(object):
    def __init__(self):
        self.H, self.D = [], None
    def add(self, entries, src):
        self.H.append((entries, src))
        assert self.D is None
        self.D = defer.Deferred()
        return self.D

class TestRecv(unittest.TestCase):
    timeout = 2

    def setUp(self):
        self.C = MockColl()
        self.fact = IOCLogServerFactory(self.C.add)
        self.P = self.fact.buildProtocol(('127.0.0.1',0))
        self.clock = self.P.reactor = task.Clock()
        self.tr = TCPStringTransport()
        self.P.makeConnection(self.tr)
        self.tr.protocol = self.P

    def test_conn(self):
        self.assertIn(self.P, self.fact.clients)
        self.assertTrue(self.tr.KA is 1)

        self.tr.loseConnection()
        self.tr = self.P = None
        import gc
        gc.collect()

        self.assertNotIn(self.P, self.fact.clients)

    def test_rx(self):
        self.P.dataReceived('line 1\n')

        # the first line received will enter the buffer
        self.assertEqual(len(self.P._B), 1)
        # and start the flush cycle
        self.assertNotIdentical(self.P._D, None)
        # but the flush won't complete yet
        self.assertIdentical(self.C.D, None)
        self.assertEqual(self.C.H, [])

        # start the flush
        self.clock.advance(self.fact.flushperiod)

        # now the buffer is emptied
        self.assertEqual(len(self.P._B), 0)
        # but the flush is still in progress
        self.assertNotIdentical(self.P._D, None)
        # because our deferred is active
        self.assertNotIdentical(self.C.D, None)
        self.assertEqual(self.C.H, [([(0.0, 'line 1')], address.IPv4Address('TCP', '192.168.1.1', 54321))])

        # complete out deferred
        self.C.D.callback(None)

        # since nothing more has been receieved the next flush isn't started
        self.assertIdentical(self.P._D, None)
        self.assertEqual(len(self.C.H), 1)

    def test_oflow1(self):
        for i in range(self.fact.buflim*2):
            self.P.dataReceived('line %d\n'%i)

        self.assertEqual(self.C.H, [])
        self.assertIdentical(self.C.D, None)
        self.assertNotIdentical(self.P._D, None)
        self.assertEqual(len(self.P._B), self.fact.buflim)
        self.assertEqual(self.P.nlost, self.fact.buflim)

    def test_oflow2(self):
        self.P.dataReceived('initial\n')

        self.assertIdentical(self.C.D, None)
        self.assertEqual(len(self.P._B), 1)

        self.clock.advance(self.fact.flushperiod)

        self.assertNotIdentical(self.C.D, None)
        self.assertEqual(len(self.P._B), 0)

        self.assertNotEqual(self.tr.producerState, 'paused')

        self.clock.advance(self.fact.flushperiod)

        self.assertEqual(len(self.P._B), 0)

        for i in range(self.fact.buflim*2):
            self.P.dataReceived('line %d\n'%i)

        self.assertNotEqual(self.C.H, [])
        self.assertNotIdentical(self.C.D, None)
        self.assertNotIdentical(self.P._D, None)
        self.assertEqual(len(self.P._B), self.fact.buflim)
