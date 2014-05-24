# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)

import os, os.path, errno

from ConfigParser import NoOptionError, NoSectionError

def rotateFile(fname, maxsize=2**20, nbackup=3):
    rotate=False
    try:
        S = os.stat(fname)
    except OSError as e:
        if e.errno!=errno.ENOENT:
            raise
    else:
        if S.st_size>maxsize:
            rotate=True

    if rotate:
        logs = ['%s.%d'%(fname,N) for N in range(nbackup)]
        logs.reverse()
        for src, dst in zip(logs[1:], logs[:-1]):
            if not os.path.isfile(src):
                continue
            if os.path.isfile(dst):
                os.remove(dst)
            _log.debug("Rotate '%s' -> '%s'", src, dst)
            os.rename(src, dst)
        assert not os.path.isfile(logs[-1])
        _log.debug("Rotate '%s' -> '%s'", fname, logs[-1])
        os.rename(fname, logs[-1])

class ConfigDict(object):
    def __init__(self, C, S):
        self._C, self._S = C, S
    @property
    def name(self):
        return self._S
    def __contains__(self, K):
        return self._C.has_option(self._S, K)
    def __getitem__(self, K):
        try:
            return self._C.get(self._S, K)
        except (NoOptionError, NoSectionError):
            raise KeyError('Missing %s'%K)
    def get(self, K, D=None):
        try:
            return self._C.get(self._S, K)
        except (NoOptionError, NoSectionError):
            return D
    def getbool(self, K, D=None):
        try:
            return self._C.getboolean(self._S, K)
        except (NoOptionError, NoSectionError):
            return D
    getboolean = getbool
    def getint(self, K, D=None):
        try:
            return self._C.getint(self._S, K)
        except (NoOptionError, NoSectionError):
            return D
