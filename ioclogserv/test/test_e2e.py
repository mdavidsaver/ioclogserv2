# -*- coding: utf-8 -*-


from twisted.trial import unittest
from twisted.internet import reactor, defer, task
from twisted.internet.protocol import Protocol, ClientFactory

from ioclogserv import collector, processor, receiver

from . import testutil

_C="""
[processor]
chain = softioc, all
[softioc]
filename=softioc.log
users= softioc
stop = true
[all]
filename=all.log
"""

class TestCollector(collector.Collector):
    """Hook into the collector to get notifications
    """
    def __init__(self, *args):
        self._flushdone, self._add = defer.Deferred(), defer.Deferred()
        super(TestCollector, self).__init__(*args)
        self.reactor = task.Clock()
    def add(self, *args):
        super(TestCollector, self).add(*args)
        D, self._add = self._add, defer.Deferred()
        D.callback(args)
    def _flushComplete(self, arg):
        R = super(TestCollector, self)._flushComplete(arg)
        self._flushdone.callback(self)
        return R

class LogClient(Protocol):
    def __init__(self):
        self.rx = []
    def connectionMade(self):
        self.factory.onconn.callback(None)
    def dataReceived(self, data):
        self.rx.append(data)

class LogClientFactory(ClientFactory):
    protocol = LogClient
    def __init__(self):
        self.onconn = defer.Deferred()
        self.P = []
    def buildProtocol(self, addr):
        P = ClientFactory.buildProtocol(self, addr)
        self.P.append(P)
        return P

_T=[
  'unformatted\n',
  '05-Apr-14 10:33:52 linacioc02 softioc BR:A4-BI{BPM:7}ddrTbtWfEnable.VAL new=1 old=1\n',
  '05-Apr-14 10:33:52 linacioc02 softioc BR:A4-BI{BPM:7}ddrTbtWfEnable.VAL new=1 old=1 min=0 max=2\n',
  '05-Apr-14 10:33:52 somewhere realperson TST{BPM:Q}ddrTbtWfEnable.VAL new=1 old=1\n',
  'some junk\n',
]


class TestEnd2End(unittest.TestCase, testutil.FileTest):
    def setUp(self):

        self.removeFile('all.log')
        self.removeFile('softioc.log')

        with open('e2e.conf','w') as F:
            F.write(_C)

        proc = processor.Processor()
        proc.load('e2e.conf')

        self.coll = coll = TestCollector(proc)

        self.fact = receiver.IOCLogServerFactory(coll)

        self.port = reactor.listenTCP(0, self.fact, interface='127.0.0.1')
        ep = self.port.getHost()

        self.fact = LogClientFactory()
        self.conn = reactor.connectTCP(ep.host, ep.port, self.fact, timeout=2)
        return self.fact.onconn

    def tearDown(self):
        self.port.stopListening()
        for P in self.fact.P:
            P.transport.loseConnection()

    @defer.inlineCallbacks
    def test_log(self):
        self.assertTrue(self.fact.P[0].connected)
        T = self.fact.P[0].transport

        T.write(''.join(_T))
        
        # wait for all entries to be add()ed to the collector
        for N in range(len(_T)):
            yield self.coll._add

        self.assertIdentical(self.coll.flushing, True)

        # advance time to trigger a flush
        self.coll.reactor.advance(20)

        self.assertNotIdentical(self.coll.flushing, True)
        self.assertTrue(self.coll.flushing)

        # wait for flush
        yield self.coll._flushdone

        self.assertFileMatch('all.log', '.*unformatted')
        self.assertFileMatch('all.log', '.*TST{BPM:Q}ddrTbtWfEnable.VAL')

        self.assertFileNotMatch('all.log', '.*softioc.*')

        self.assertFileMatch('softioc.log', '.*softioc.*')

        self.assertFileNotMatch('softioc.log', '.*unformatted')
        self.assertFileNotMatch('softioc.log', '.*TST{BPM:Q}ddrTbtWfEnable.VAL')
