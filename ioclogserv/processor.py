# -*- coding: utf-8 -*-

import logging
_log = logging.getLogger(__name__)

import re

from . import handler

from twisted.internet import defer, threads

# DD-Mon-YY HH:MM:SS host user PV new=A old=B [min=C max=D]
_capl = r'(?P<time>\d+-\S+-\d+ \d+:\d+:\d+) (?P<host>\S+) (?P<user>\S+) (?P<pv>\S+)' + \
        r'.*'
#        r' new=(?P<new>\S*) old=(?P<old>\S*) (?:min=(?P<min>\S*) max=(?P<max>\S*))?'

_capl=re.compile(_capl)

class PutLogTagger(handler.Processor):
    @defer.inlineCallbacks
    def process(self, entries):
        # do regex processing in a worker thread
        entries = yield threads.deferToThread(self._onthread, entries)
        yield self.complete(entries)

    def _onthread(self, entries):
        for ent in entries:
            M = _capl.match(ent.msg)
            if M:
                ent.user = M.group('user')
                ent.host = M.group('host')
                ent.pv = M.group('pv')
            else:
                ent.user = ent.host = ent.pv = None
        return entries

handler.registerProcessor('tagcaputlog', PutLogTagger)

class PutLogFilter(handler.Processor):
    def __init__(self, conf=None):
        handler.Processor.__init__(self, conf)
        self.puser, self.nuser = set(), set()
        if 'user' not in conf:
            _log.warning('putlog filter with no user spec')
            return

        for user in map(str.strip, conf['user'].split()):
            G = self.puser
            if user.startswith('-'):
                G = self.nuser
                user = user[1:]
            elif user.startswith('+'):
                user = user[1:]

            if user=='None':
                user = None # catchall for entries not in caputlog format

            G.add(user)

        if self.puser and self.nuser:
            _log.warn("Giving both positive and negative user matches isn't helpful")

    @defer.inlineCallbacks
    def process(self, entries):
        result = []
        for ent in entries:
            if self.puser and ent.user in self.puser:
                result.append(ent)
            elif self.nuser and ent.user not in self.nuser:
                result.append(ent)
        yield self.complete(result)

handler.registerProcessor('filtercaputlog', PutLogFilter)
