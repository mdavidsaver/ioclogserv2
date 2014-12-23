# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)
from logging.handlers import RotatingFileHandler

import os.path

from . import handler

class FileWriter(handler.DecouplingProcessor):
    _fmt = '%(source)s %(asctime)s %(message)s'
    _date = '%a %b %d %H:%M:%S %Y'
    def __init__(self, conf=None):
        handler.DecouplingProcessor.__init__(self, conf)
        fname = conf['filename']
        if not os.path.isdir(os.path.dirname(fname)):
            _log.warn("Log file directory doesn't: %s", fname)
        self.H = None

    def startService(self):
        # Don't create RotatingFileHandler until privlages are dropped
        fname = self.conf['filename']
        maxBytes = self.conf.getint('maxsize', 10*1024*1024)
        backupCount = self.conf.getint('maxfiles', 10)
        H = RotatingFileHandler(fname, maxBytes=maxBytes,
                                backupCount=backupCount)
        H.setFormatter(logging.Formatter(self._fmt,self._date))

        self.H = H

        return handler.Processor.startService(self)

    def process_queue(self, entries):
        for E in entries:
            self.H.emit(E)

handler.registerProcessor('writer', FileWriter)
