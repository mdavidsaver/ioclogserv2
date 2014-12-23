# -*- coding: utf-8 -*-

from zope import interface

import logging
_log = logging.getLogger(__name__)

from cStringIO import StringIO

from twisted.application import service
from twisted.internet import defer, reactor, task

from .util import ConfigDict

def makeRecord(msg, *args):
    R = logging.LogRecord(None,logging.INFO, '',0,
                          msg, args, None, None)

    # our extra attributes for all records
    R.source = None
    return R

class Processor(service.MultiService):
    generator = False
    complete = None

    def __init__(self, conf=None):
        service.MultiService.__init__(self)
        self.conf = conf
        self.dst = []

    def process(self, entries):
        return self.complete(entries)

    def complete(self, entries):
        if len(entries)==0:
            return defer.succeed(None)

        Ds = []
        for cb in self.dst:
            Ds.append(defer.maybeDeferred(cb.process, entries))

        D = defer.DeferredList(Ds, fireOnOneErrback=True)
        @D.addErrback
        def fail(F):
            # unwrap FirstError
            E = F.trap(defer.FirstError)
            if E is defer.FirstError:
                F = F.subFailure
            return F

        return D

class DecouplingProcessor(Processor):
    reactor = reactor
    def __init__(self, conf=None):
        Processor.__init__(self,conf)
        self.flushperiod = conf.getfloat('buffer.period',5.0)
        self.buflim = conf.getint('buffer.size', 100)
        self._B, self._D = [], None
        self.nlost = 0

        if self.buflim==0:
            # disable buffering and run blocking
            self.process = self.process_queue

    def process(self, entries):
        if len(self._B)>=self.buflim:
            self.nlost += len(entries)
            return # drop

        self._B.extend(entries)
        if self._D is None:
            self._start_flush()

    def process_queue(self, entries):
        return self.complete(entries)

    def _start_flush(self):
        assert self._D is None
        self._D = task.deferLater(self.reactor, self.flushperiod,
                                      self._flush)

        @self._D.addErrback
        def oops(F):
            self._D = None
            S = StringIO()
            F.printDetailedTraceback(S)
            _log.error(S.getvalue())

    @defer.inlineCallbacks
    def _flush(self):
        B, self._B = self._B, []
        nlost, self.nlost = self.nlost, 0
        _log.debug('Flush %d messages at %s', len(B), self.name)
        if nlost>0:
            B.append(makeRecord('Lost %d messages at %s', nlost,self.name))

        yield self.process_queue(B)
        self._D = None
        if len(self._B)>0:
            self._start_flush()

_factories = {
    'decouple':DecouplingProcessor,
}

def registerProcessor(name, klass):
    assert service.IService in interface.implementedBy(klass)
    _factories[name] = klass

def buildProcessor(name, dict):
    klass = _factories[dict['type']]
    return klass(conf=dict)

def buildPipelines(parser):
    byname = {}
    S = service.MultiService()

    # Construct all processors
    for sect in parser.sections():
        conf = ConfigDict(parser, sect)
        if 'type' not in conf:
            continue

        proc = buildProcessor(sect, conf)
        proc.setName(sect)

        byname[sect] = proc
        S.addService(proc)

    roots = {}

    # Connect to sources
    for proc in byname.itervalues():
        if 'in' not in proc.conf:
            if not proc.generator:
                raise RuntimeError("No source for %s which isn't a generator"%proc.name)
            roots[proc.name] = proc

        else:
            src = byname.get(proc.conf['in'])
            if src is None:
                raise RuntimeError("Source %s for %s doesn't exist"%(proc.conf['in'],proc.name))
            src.dst.append(proc)

    return [S], byname
