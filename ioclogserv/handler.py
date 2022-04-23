# -*- coding: utf-8 -*-

from zope import interface

import logging
_log = logging.getLogger(__name__)

from twisted.application import service
from twisted.internet import defer

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
        """Do processing work of this plugin.
        
        Default implementation calls self.complete(entries) to pass
        results along to chained plugins.
        Should return a deferred which fires when all work is complete
        (may use the return value of self.complete()).
        """
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
                try:
                    F = F.subFailure
                #twistd-19.10.0: 'Failure' object has no attribute 'subFailure'
                except: 
                    F = E 
            return F

        return D

    def __repr__(self):
        return '%s(name="%s")'%(self.__class__.__name__, self.name)
    __str__ = __repr__

_factories = {}

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
    #for proc in byname.itervalues():
    for proc in byname.values():
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
