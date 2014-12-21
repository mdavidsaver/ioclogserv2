# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)

from ConfigParser import NoOptionError, NoSectionError

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
    def getfloat(self, K, D=None):
        try:
            return self._C.getfloat(self._S, K)
        except (NoOptionError, NoSectionError):
            return D
