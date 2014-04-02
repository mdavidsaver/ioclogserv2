# -*- coding: utf-8 -*-

from twisted.trial import unittest
from twisted.test import proto_helpers

from ioclogserv.receiver import IOCLogServerFactory

class TCPStringTransport(proto_helpers.StringTransportWithDisconnection):
    def __init__(self):
        proto_helpers.StringTransportWithDisconnection.__init__(self)
        self.KA = None
    def setTcpKeepAlive(self, V):
        self.KA = V

class MockColl(object):
    def __init__(self):
        self.H, self.cli = [], set()
        self.connect = self.cli.add
        self.disconnect = self.cli.remove
    def add(self, src, peer, line, rxtime):
        self.H.append((src, peer, line, rxtime))

class TestRecv(unittest.TestCase):
    def setUp(self):
        self.C = MockColl()
        fact = IOCLogServerFactory(self.C)
        self.P = fact.buildProtocol(('127.0.0.1',0))
        self.tr = TCPStringTransport()
        self.P.makeConnection(self.tr)
        self.tr.protocol = self.P

    def test_conn(self):
        self.assertIn(self.P, self.C.cli)
        self.assertTrue(self.tr.KA is 1)

        self.tr.loseConnection()
        
        self.assertNotIn(self.P, self.C.cli)

    def test_rx(self):
        self.P.dataReceived('line 1\n')

        self.assertEqual(len(self.C.H), 1)
        self.assertEqual(self.C.H[0], (self.P, self.tr.getPeer(), 'line 1', self.C.H[0][3]))

    def test_rate(self):
        self.assertEqual(self.tr.producerState, 'producing')

        for N in range(self.P.Nlim+5):
            self.P.dataReceived('line %d\n'%N)

        self.assertEqual(self.tr.producerState, 'paused')

        self.assertEqual(len(self.C.H), self.P.Nlim)

        self.P.ack()
        self.assertEqual(self.tr.producerState, 'producing')
