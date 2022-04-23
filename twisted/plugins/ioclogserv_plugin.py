# -*- coding: utf-8 -*-

import logging, sys

try:
    from ConfigParser import SafeConfigParser as ConfigParser #py2.7
except ImportError:
    from configparser import SafeConfigParser as ConfigParser

from twisted.python import log
from twisted.application.internet import TCPServer
try:
    from twisted.manhole.telnet import ShellFactory
except ImportError:
    ShellFactory = None

from ioclogserv import forward, handler, processor, receiver, store, util

#from zope.interface import implements
from zope.interface import implementer

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import service

class Log2Twisted(logging.StreamHandler):
    """Print logging module stream to the twisted log
    """
    def __init__(self):
        logging.StreamHandler.__init__(self,self)
        self.write = log.msg
    def flush(self):
        pass

class Options(usage.Options):
    optFlags = [
        ["debug", "d", "Run daemon in developer (noisy) mode"],
    ]
    optParameters = [
        ['config', 'C', "server.conf", "Configuration file"],
        ['manhole', 'M', 0, "Manhole port (default not-run)", int],
    ]
    def postOptions(self):
        C = ConfigParser()
        print('Reading',self['config'])
        with open(self['config'], 'r') as F:
            C.readfp(F)
        self['config'] = C

def showService(S,i=1):
    print(' '*i,S)
    if hasattr(S, 'services'):
        [showService(SS,i+1) for SS in S.services]

@implementer(service.IServiceMaker, IPlugin)
class Maker(object):
    #implements(service.IServiceMaker, IPlugin)
    tapname = 'ioclogserver'
    description = "IOC Log Server"
    options = Options

    def makeService(self, opts):
        tempH = logging.StreamHandler(sys.stderr)
        tempH.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

        H = Log2Twisted()
        H.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

        R = logging.getLogger()
        R.addHandler(tempH)
        R.addHandler(H)

        conf = opts['config']
        gen = util.ConfigDict(conf, 'general')
        lvl = logging.getLevelName(gen.get('log.level','WARN'))
        R.setLevel(lvl)

        serv = service.MultiService()

        roots, services = handler.buildPipelines(conf)
        [serv.addService(S) for S in roots]

        for S in services.values():
            print(S.name,S)

        if ShellFactory and opts['manhole']:
            print('Opening Manhole')
            SF = ShellFactory()
            SF.namespace.update(services)

            SS = TCPServer(opts['manhole'], SF, interface='127.0.0.1')
            serv.addService(SS)

        R.removeHandler(tempH)
        print('root service',serv)
        showService(serv)
        return serv

serviceMaker = Maker()
