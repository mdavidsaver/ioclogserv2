# -*- coding: utf-8 -*-

import re, time, os, os.path, errno

from twisted.python import log
from twisted.internet import threads, reactor, defer

class Collector(object):
    """Aggregates log entries and initiates processing
    in a worker thread
    """
    def __init__(self, processor, reactor=reactor):
        self.proc, self.reactor = processor, reactor
        self.sizelimit, self.nrot = 100*2**20, 4
        self.Nflush, self.Nlimit, self.Tflush = 10, 20, 30
        self.flushing = None
        self.buf = []

        self.clients = set()
        self.connect = self.clients.add
        self.disconnect = self.clients.remove

    def _doFlush(self):
        assert not isinstance(self.flushing, defer.Deferred)
        N = len(self.buf)
        # if buffer size is over flush threshold, or time contained
        # in buffer is longer than flush interval
        if N>=self.Nflush or (N>=2 and self.buf[-1][3]-self.buf[0][3]>self.Tflush):
            self.flushing = True
            self.reactor.callLater(self.Tflush/2, self._startFlush)

    def _startFlush(self):
        self.buf, buf = [], self.buf
        self.flushing = D = threads.deferToThread(self.proc.proc, buf)
        D.addBoth(self._flushComplete)

    def add(self, src, client, line, rxtime):
        """Add a new log entry to the queue
        """
        if self.flushing and len(self.buf)>=self.Nlimit:
            # Flush in progress, so we don't want to buffer too many
            if len(self.buf)==self.Nlimit:
                self.buf.append((None, None, 'messages lost', time.time()))
            return
        self.buf.append((src, client, line, rxtime))
        if self.flushing:
            return
        self._doFlush()

    def _flushComplete(self, arg):
        self.flushing = None
        for C in self.clients:
            C.ack() # resume recv() if necessary
        self._doFlush()
        return arg
