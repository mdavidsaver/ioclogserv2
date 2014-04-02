# -*- coding: utf-8 -*-

import time

from twisted.python import log
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineOnlyReceiver

class IOCLogServer(LineOnlyReceiver):
    """Communicate with an individual client (IOC)
    """
    delimiter = b'\n'
    def __init__(self, coll):
        self.N, self.Nlim, self.paused, self.collector = 0, 30, False, coll
        self.logstr = '<unassociated>'
    def logPrefix(self):
        return self.logstr
    def connectionMade(self):
        self.transport.setTcpKeepAlive(1)
        self.peer = self.transport.getPeer()
        self.logstr = 'client %s'%self.peer
        self.collector.connect(self)
        log.msg('connected')
    def connectionLost(self, reason=None):
        self.collector.disconnect(self)
        log.msg('disconnected: %s'%reason)
        self.logstr = 'client %s (disconnected)'%self.peer
        self.peer = None
    def lineLengthExceeded(self, line):
        self.lineReceived('Line length exceeded')
    def lineReceived(self, line):
        if self.N >= self.Nlim:
            log.msg('throttled')
            self.transport.pauseProducing()
            self.paused = True
            return
        self.N += 1
        self.collector.add(self, self.peer, line, time.time())
    def ack(self):
        log.msg('ack')
        self.N = 0
        if self.paused:
            log.msg('resumed')
            self.transport.resumeProducing()
            self.paused = False

class IOCLogServerFactory(ServerFactory):
    protocol = IOCLogServer
    def __init__(self, collector):
        self.collector = collector
    def buildProtocol(self, addr):
        return self.protocol(self.collector)
