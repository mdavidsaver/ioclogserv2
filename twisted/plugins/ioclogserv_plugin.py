# -*- coding: utf-8 -*-

from twisted.application.internet import TCPServer
try:
    from twisted.manhole.telnet import ShellFactory
except ImportError:
    ShellFactory = None

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
        ['port', 'P', 7004, "Port to listen on (default 7004)", int],
        ['config', 'C', "server.conf", "Configuration file"],
        ['manhole', 'M', 2222, "Manhole port (default not-run)", int],
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
        for E in proc.dest:
            print 'Destination',E.name
            print ' Maxsize:',E._maxsize
            print ' Backups:',E._nbackup

        coll = collector.Collector(proc)

        fact = receiver.IOCLogServerFactory(coll)

        if opts['debug']:
            print 'Running in developer (noisy) mode'
            coll.Tflush = 3
            coll.debug = True

        print 'Starting logserver.'

        serv = service.MultiService()
        serv.addService(TCPServer(opts['port'], fact))

        if ShellFactory and opts['manhole']:
            print 'Opening Manhole'
            SF = ShellFactory()
            SS = TCPServer(opts['manhole'], SF, interface='127.0.0.1')

            SF.namespace['proc'] = proc
            SF.namespace['coll'] = coll
            SF.namespace['fact'] = fact

            serv.addService(SS)

        return serv

serviceMaker = Maker()
