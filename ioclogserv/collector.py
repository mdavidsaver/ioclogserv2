# -*- coding: utf-8 -*-

import time

from twisted.python import log
from twisted.internet import threads, reactor, defer

class Collector(object):
    """Aggregates log entries and initiates processing
    in a worker thread
    """
    def __init__(self, processor, reactor=reactor):
        self.proc, self.reactor, self.debug = processor, reactor, False
        self.Nlimit, self.Tflush = 5000, 10
        self.flushing = None
        self.buf = []
        self.nlost = 0

        self.clients = set()
        self.connect = self.clients.add
        self.disconnect = self.clients.remove

    def _doFlush(self):
        assert not isinstance(self.flushing, defer.Deferred)
        if len(self.buf) and self.flushing is None:
            self.flushing = True
            self.reactor.callLater(self.Tflush, self._startFlush)

    def _startFlush(self):
        if self.debug:
            log.msg('Start flush')
        assert self.flushing is True
        self.buf, buf = [], self.buf
        if self.nlost:
            self.buf.append((None, None, '%d messages lost'%self.nlost, time.time()))
            self.nlost = 0
        self.flushing = D = threads.deferToThread(self.proc.proc, buf)
        D.addBoth(self._flushComplete)

    def add(self, src, client, line, rxtime):
        """Add a new log entry to the queue
        """
        if len(self.buf)>=self.Nlimit:
            self.nlost += 1
            return
        if self.debug:
            log.msg('%d From %s: %s'%(rxtime, client, line))
        self.buf.append((src, client, line, rxtime))
        if self.flushing:
            return
        self._doFlush()

    def _flushComplete(self, arg):
        if self.debug:
            log.msg('Complete flush')
        self.flushing = None
        for C in self.clients:
            C.ack() # resume recv() if necessary
        self._doFlush()
        return arg
