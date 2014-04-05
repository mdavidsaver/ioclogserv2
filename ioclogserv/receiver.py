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
    def connectionMade(self):
        self.transport.setTcpKeepAlive(1)
        self.peer = self.transport.getPeer()
        self.collector.connect(self)
        log.msg('connected %s:%d'%(self.peer.host, self.peer.port))
    def connectionLost(self, reason=None):
        self.collector.disconnect(self)
        log.msg('disconnected')
        self.peer = None
    def lineLengthExceeded(self, line):
        self.lineReceived('Line length exceeded')
    def lineReceived(self, line):
        if self.N >= self.Nlim:
            self.transport.pauseProducing()
            self.paused = True
            return
        self.N += 1
        self.collector.add(self, self.peer, line, time.time())
    def ack(self):
        self.N = 0
        if self.paused:
            self.transport.resumeProducing()
            self.paused = False

class IOCLogServerFactory(ServerFactory):
    protocol = IOCLogServer
    def __init__(self, collector):
        self.collector = collector
    def buildProtocol(self, addr):
        return self.protocol(self.collector)
