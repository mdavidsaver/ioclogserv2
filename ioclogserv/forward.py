# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)

from twisted.application import internet
from twisted.internet import protocol

from . import handler

class SendOnly(protocol.Protocol):
    publisher = None
    def connectionMade(self):
        self.publisher.add(self.transport)
        _log.info('Add Subscriber %s', self.transport.getPeer())
    def connectionLost(self, res=None):
        _log.info('Del Subscriber %s', self.transport.getPeer())
        self.publisher.remove(self.transport)
    def dataReceived(self, data):
        pass # ignore

class PublisherFactory(protocol.ServerFactory):
    protocol = SendOnly
    publisher = None
    def buildProtocol(self, addr):
        P = self.protocol()
        P.publisher = self.publisher
        return P

# 10.0.152.88:51393 Sun Dec 21 10:58:21 2014 21-Dec-14 10:58:14 cdesk05 wguo RF{Osc:1}Freq:SP.VAL new=0.499682 old=0.499682 min=0.499682 max=0.499682

class NetPublisher(handler.Processor):
    _fmt = '%(source)s %(asctime)s %(message)s'
    _date = '%a %b %d %H:%M:%S %Y'
    def __init__(self, conf=None):
        handler.Processor.__init__(self, conf)

        self.fact = PublisherFactory()
        self.fact.publisher = self
        self.clients = []
        self.fmt = logging.Formatter(self._fmt, self._date)

        self.serv = internet.TCPServer(conf.getint('port',7014), self.fact,
                                       interface=conf.get('addr',''))

        self.addService(self.serv)

    # flow control for individual recipients.
    # If production exceeds consumption then messages are dropped and
    # the number of dropped entries is recorded.
    class Producer(object):
        def __init__(self, tr):
            self.transport = tr
            self.paused, self.nlost = False, 0
        def resumeProducing(self):
            self.paused = False
        def pauseProducing(self):
            self.paused = True
        stopProducing = pauseProducing

    def add(self, clienttr):
        P = self.Producer(clienttr)
        clienttr.registerProducer(P, True)
        clienttr.__producer = P
        self.clients.append(P)

    def remove(self, clienttr):
        P = clienttr.__producer
        clienttr.unregisterProducer()
        del clienttr.__producer
        self.clients.remove(P)

    def process(self, entries):
        entries = ''.join([self.fmt.format(E)+'\n' for E in entries])
        for P in self.clients:
            if P.paused:
                P.nlost += len(entries)
                continue

            elif P.nlost>0:
                P.transport.write('Lost %d entries at %s\n'%(P.nlost,self.name))
                P.nlost=0

            try:
                P.transport.write(entries)
            except:
                # on error, disconnect the offending client and continue
                _log.exception('Error writing to %s', P.transport.getPeer())
                P.transport.loseConnection()


handler.registerProcessor('sender', NetPublisher)
