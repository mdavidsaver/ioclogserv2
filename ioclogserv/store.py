# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)
from logging.handlers import RotatingFileHandler

import os.path

from twisted.internet import defer, reactor, threads

from . import handler

class FileWriter(handler.Processor):
    reactor = reactor
    _fmt = '%(source)s %(asctime)s %(message)s'
    _date = '%a %b %d %H:%M:%S %Y'
    def __init__(self, conf=None):
        handler.Processor.__init__(self, conf)
        fname = conf['filename']
        if not os.path.isdir(os.path.dirname(fname)):
            _log.warn("Log file directory doesn't: %s", fname)
        self.H = None
        self.L = defer.DeferredLock()

    def startService(self):
        # Don't create RotatingFileHandler until privlages are dropped
        fname = self.conf['filename']
        maxBytes = self.conf.getint('maxsize', 10*1024*1024)
        backupCount = self.conf.getint('numbackup', 10)
        H = RotatingFileHandler(fname, maxBytes=maxBytes,
                                backupCount=backupCount)
        H.setFormatter(logging.Formatter(self._fmt,self._date))

        self.H = H

        return handler.Processor.startService(self)

    @defer.inlineCallbacks
    def process(self, entries):
        assert self.H is not None, 'process before startService'
        # avoid concurrent writes and associated corruption
        yield self.L.acquire()
        try:
            # defer blocking file I/O to a worker thread
            yield threads.deferToThread(self._doWrite, entries)
        finally:
            # drop back to the reactor to do the next write
            self.reactor.callLater(0, self.L.release)

    def _doWrite(self, entries): # called from worker thread
        for E in entries:
            self.H.emit(E)

handler.registerProcessor('writer', FileWriter)
