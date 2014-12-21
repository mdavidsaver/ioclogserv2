# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)

from twisted.application import internet
from twisted.internet import protocol

from . import handler

class SendOnly(protocol.Protocol):
    publisher = None
    def connectionMade(self):
        self.publisher.clients.add(self.transport)
        _log.info('Add Subscriber %s', self.transport.getPeer())
    def connectionLost(self, res=None):
        _log.info('Del Subscriber %s', self.transport.getPeer())
        self.publisher.clients.remove(self.transport)
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

class NetPublisher(handler.DecouplingProcessor):
    _fmt = '%(source)s %(asctime)s %(message)s'
    _date = '%a %b %d %H:%M:%S %Y'
    def __init__(self, conf=None):
        handler.DecouplingProcessor.__init__(self, conf)

        self.fact = PublisherFactory()
        self.fact.publisher = self
        self.clients = set()
        self.fmt = logging.Formatter(self._fmt, self._date)

        self.serv = internet.TCPServer(conf.getint('port',7014), self.fact,
                                       interface=conf.get('addr',''))

        self.addService(self.serv)
    
    def process_queue(self, entries):
        entries = ''.join([self.fmt.format(E)+'\n' for E in entries])
        for C in self.clients:
            try:
                C.write(entries)
            except:
                _log.exception('Error writing to %s', C.getPeer())
                C.loseConnection()


handler.registerProcessor('sender', NetPublisher)
