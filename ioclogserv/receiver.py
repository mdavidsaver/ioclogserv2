# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)

import weakref

from twisted.internet import defer, protocol, reactor, task
from twisted.protocols import basic

class IOCLogProtocol(basic.LineOnlyReceiver):
    """Communicate with an individual client (IOC)
    """
    reactor = reactor
    delimiter = b'\n'
    buflim = 30
    collector = None
    flushperiod = 1.0

    def connectionMade(self):
        self._B, self._D, self.paused = [], None, False
        self.pausecnt = 0

        self.transport.setTcpKeepAlive(1)
        self.peer = self.transport.getPeer()
        _log.info('connected %s:%d'%(self.peer.host, self.peer.port))

    def connectionLost(self, reason=None):
        _log.info('disconnected')
        self.peer = None

    def lineLengthExceeded(self, line):
        self.lineReceived('Line length exceeded')

    def lineReceived(self, line):
        self._B.append((self.reactor.seconds(), line))

        if self._D is None:
            self._D = task.deferLater(self.reactor, self.flushperiod,
                                      self._flush)

        if not self.paused and len(self._B)>=self.buflim:
            self.transport.pauseProducing()
            self.paused = True
            self.pausecnt += 1
            _log.debug('Pause %s:%d', self.peer.host, self.peer.port)

    def _unpause(self):
        if self.paused:
            self.transport.resumeProducing()
            self.paused = False
            _log.debug('Resume %s:%d', self.peer.host, self.peer.port)

    @defer.inlineCallbacks
    def _flush(self):
        B, self._B = self._B, []
        self._unpause()
        T0 = self.reactor.seconds()
        yield defer.maybeDeferred(self.collector, B, self.peer)

        T1 = self.reactor.seconds()
        if len(self._B)>0:
            self._D = task.deferLater(self.reactor, self.flushperiod,
                                      self._flush)
        else:
            self._unpause()
            self._D = None

        dT = T1-T0
        if dT*0.9>self.flushperiod:
            _log.warn("Processing %d messages from %s:%d took %f%%",
                      len(B), self.peer.host, self.peer.port,
                      100.0*dT/self.flushperiod)

class IOCLogServerFactory(protocol.ServerFactory):
    protocol = IOCLogProtocol
    def __init__(self, collector):
        self.collector = collector
        self.clients = weakref.WeakSet()

    def buildProtocol(self, addr):
        P = self.protocol()
        P.collector = self.collector
        self.clients.add(P)
        return P
