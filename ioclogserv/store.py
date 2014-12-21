# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)
from logging.handlers import RotatingFileHandler

from . import handler

class FileWriter(handler.DecouplingProcessor):
    _fmt = '%(source)s %(asctime)s %(message)s'
    _date = '%a %b %d %H:%M:%S %Y'
    def __init__(self, conf=None):
        handler.DecouplingProcessor.__init__(self, conf)
        fname = conf['filename']
        maxBytes = conf.getint('maxsize', 10*1024*1024)
        backupCount = conf.getint('maxfiles', 10)
        H = RotatingFileHandler(fname, maxBytes=maxBytes,
                                backupCount=backupCount)
        H.setFormatter(logging.Formatter(self._fmt,self._date))

        self.H = H

    def process_queue(self, entries):
        for E in entries:
            self.H.emit(E)

handler.registerProcessor('writer', FileWriter)
