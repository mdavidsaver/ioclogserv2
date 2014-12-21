# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)

import weakref
from cStringIO import StringIO

from twisted.application import internet
from twisted.internet import defer, protocol, reactor, task
from twisted.protocols import basic

from . import handler

class IOCLogProtocol(basic.LineOnlyReceiver):
    """Communicate with an individual client (IOC)
    """
    reactor = reactor
    delimiter = b'\n'
    collector = None

    def connectionMade(self):
        self._B, self._D = [], None
        self.nlost = 0

        self.transport.setTcpKeepAlive(1)
        self.peer = self.transport.getPeer()
        _log.info('connected %s:%d'%(self.peer.host, self.peer.port))

    def connectionLost(self, reason=None):
        _log.info('disconnected %s:%d'%(self.peer.host, self.peer.port))

    def lineLengthExceeded(self, line):
        self.lineReceived('Line length exceeded')

    def lineReceived(self, line):
        if len(self._B)>=self.factory.buflim:
            # must receive as fast as possible to avoid blocking
            # the sender as this will cause ioclog
            # to lose more message locally!
            # So we receive and discard
            self.nlost += 1
            return

        self._B.append((self.reactor.seconds(), line))

        if self._D is None:
            self._start_flush()

    def _start_flush(self):
        assert self._D is None
        self._D = task.deferLater(self.reactor, self.factory.flushperiod,
                                      self._flush)

        @self._D.addErrback
        def oops(F):
            self._D = None
            S = StringIO()
            F.printDetailedTraceback(S)
            _log.error(S.getvalue())

    @defer.inlineCallbacks
    def _flush(self):
        B, self._B = self._B, []
        nlost, self.nlost = self.nlost, 0
        _log.debug('Flush %d messages from %s:%d at %s', len(B),
                   self.peer.host, self.peer.port, self.factory.name)
        if nlost>0:
            B.append((self.reactor.seconds(), 'Lost %d messages at %s'%(nlost,self.factory.name)))

        T0 = self.reactor.seconds()
        yield defer.maybeDeferred(self.collector, B, self.peer)

        T1 = self.reactor.seconds()

        dT = T1-T0
        if dT*0.9>self.factory.flushperiod:
            _log.warn("Processing %d messages at %s from %s:%d took %f%%",
                      len(B), self.factory.name,
                      self.peer.host, self.peer.port,
                      100.0*dT/self.factory.flushperiod)

        self._D = None
        if len(self._B)>0:
            self._start_flush()

class IOCLogServerFactory(protocol.ServerFactory):
    protocol = IOCLogProtocol

    # instance default set by Processor
    name = 'receiver'
    buflim = 30
    flushperiod = 1.0

    def __init__(self, collector):
        self.collector = collector
        self.clients = weakref.WeakSet()

    def buildProtocol(self, addr):
        P = self.protocol()
        P.factory = self
        P.collector = self.collector
        self.clients.add(P)
        return P

class IOCLogReceiver(handler.Processor):
    generator = True
    def __init__(self, conf=None):
        handler.Processor.__init__(self,conf)
        self.fact = IOCLogServerFactory(self._process)

        self.fact.flushperiod = conf.getfloat('buffer.period',1.0)
        self.fact.buflim = conf.getint('buffer.size', 100)

        self.serv = internet.TCPServer(conf.getint('port',7004), self.fact,
                                       interface=conf.get('addr',''))

        self.addService(self.serv)

    def serviceStart(self):
        handler.Processor.serviceStart(self)
        self.fact.name = self.name

    @defer.inlineCallbacks
    def _process(self, entries, src):
        src = '%s:%d'%(src.host,src.port)
        ret = [None]*len(entries)
        for i,(T,msg) in enumerate(entries):
            R = logging.LogRecord('', logging.INFO, "", 0, msg, (), None, None)
            R.created = T
            R.source = src
            ret[i] = R

        yield self.complete(ret)

handler.registerProcessor('receiver', IOCLogReceiver)
