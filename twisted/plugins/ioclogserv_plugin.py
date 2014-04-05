# -*- coding: utf-8 -*-

from twisted.application.internet import TCPServer

from ioclogserv import collector, processor, receiver

import os.path

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import service

class Options(usage.Options):
    optFlags = [
        ["debug", "d", "Run daemon in developer (noisy) mode"],
    ]
    optParameters = [
        ['ip', '', "", "Address of interface to bind (default all)"],
        ['port', 'P', 7004, "Address of interface to bind (default all)", int],
        ['config', 'C', "server.conf", "Configuration file"],
    ]
    def postOptions(self):
        if self['port'] < 1 or self['port'] > 65535:
            raise usage.UsageError('Port out of range')
        if not self['config'] or not os.path.isfile(self['config']):
            raise usage.UsageError('"%s" does not exist'%self['config'])

class Maker(object):
    implements(service.IServiceMaker, IPlugin)
    tapname = 'ioclogserver'
    description = "IOC Log Server"
    options = Options

    def makeService(self, opts):

        proc = processor.Processor()
        proc.load(opts['config'])

        coll = collector.Collector(proc)

        fact = receiver.IOCLogServerFactory(coll)

        if opts['debug']:
            print 'Running in developer (noisy) mode'
            coll.Tflush = 3
            coll.debug = True

        return TCPServer(opts['port'], fact)

serviceMaker = Maker()
