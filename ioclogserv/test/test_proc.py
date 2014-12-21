# -*- coding: utf-8 -*-

import logging

from twisted.trial import unittest
from twisted.internet import defer


from .. import handler, processor

class Store(object):
    def __init__(self):
        self.entries = []
    def process(self, entries):
        self.entries.append(entries)
        return defer.succeed(None)

_other='some random line'
_L='05-Apr-14 10:33:52 linacioc02 softioc BR:A4-BI{BPM:7}ddrTbtWfEnable.VAL new=1 old=1'
_M='05-Apr-14 10:33:52 linacioc02 softioc BR:A4-BI{BPM:7}ddrTbtWfEnable.VAL new=1 old=1 min=0 max=2'

class TestTagger(unittest.TestCase):
    timeout = 2

    def setUp(self):
        self.P = processor.PutLogTagger({})
        self.S = Store()
        self.P.dst.append(self.S)

    @defer.inlineCallbacks
    def test_nocapl(self):
        M = logging.LogRecord(None, logging.INFO, '', 0, _other, (), None, None)
        yield self.P.process([M])
        self.assertEqual(len(self.S.entries), 1)
        self.assertEqual(len(self.S.entries[0]), 1)
        E = self.S.entries[0][0]
        self.assertIdentical(E.user, None)
        self.assertIdentical(E.host, None)
        self.assertIdentical(E.pv, None)

    @defer.inlineCallbacks
    def test_capl(self):
        Es = [logging.LogRecord(None, logging.INFO, '', 0, M, (), None, None)
                for M in [_L,_M]]
        yield self.P.process(Es)
        self.assertEqual(len(self.S.entries), 1)
        self.assertEqual(len(self.S.entries[0]), 2)
        for E in self.S.entries[0]:
            self.assertEqual(E.user, 'softioc')
            self.assertEqual(E.host, 'linacioc02')
            self.assertEqual(E.pv, 'BR:A4-BI{BPM:7}ddrTbtWfEnable.VAL')

class TestFilter(unittest.TestCase):
    timeout = 2

    @defer.inlineCallbacks
    def test_pos_None(self):
        self.S = Store()
        self.P = processor.PutLogFilter({'user':'+None'})
        self.P.dst.append(self.S)

        self.assertEqual(self.P.puser, {None})

        R = handler.makeRecord('something else')
        R.user = None
        yield self.P.process([R])

        self.assertEqual(len(self.S.entries), 1)
        self.assertEqual(len(self.S.entries[0]), 1)
        self.assertIdentical(self.S.entries[0][0].user, None)

    @defer.inlineCallbacks
    def test_neg_None(self):
        self.S = Store()
        self.P = processor.PutLogFilter({'user':'-None'})
        self.P.dst.append(self.S)

        self.assertEqual(self.P.nuser, {None})

        R = [handler.makeRecord('something else'),handler.makeRecord('other')]
        R[0].user = None
        R[1].user = 'other'
        yield self.P.process(R)

        self.assertEqual(len(self.S.entries), 1)
        self.assertEqual(len(self.S.entries[0]), 1)
        self.assertEqual(self.S.entries[0][0].user, 'other')

    @defer.inlineCallbacks
    def test_pos_user(self):
        self.S = Store()
        self.P = processor.PutLogFilter({'user':'one +two'})
        self.P.dst.append(self.S)

        self.assertEqual(self.P.puser, {'one','two'})

        Es = []
        for i,user in enumerate(['random','one','fakeone','twothree','two']):
            M = logging.LogRecord(None, logging.INFO, '', 0, 'msg %d %s', (i,user), None, None)
            M.user = user
            M.i = i
            Es.append(M)

        yield self.P.process(Es)
        self.assertEqual(len(self.S.entries), 1)
        self.assertEqual(len(self.S.entries[0]), 2)
        self.assertEqual(self.S.entries[0][0].i, 1)
        self.assertEqual(self.S.entries[0][1].i, 4)

    @defer.inlineCallbacks
    def test_neg_user(self):
        self.S = Store()
        self.P = processor.PutLogFilter({'user':'-one -two'})
        self.P.dst.append(self.S)

        self.assertEqual(self.P.nuser, {'one','two'})

        Es = []
        for i,user in enumerate(['random','one','fakeone','twothree','two']):
            M = logging.LogRecord(None, logging.INFO, '', 0, 'msg %d %s', (i,user), None, None)
            M.user = user
            M.i = i
            Es.append(M)

        yield self.P.process(Es)
        self.assertEqual(len(self.S.entries), 1)
        self.assertEqual(len(self.S.entries[0]), 3)
        self.assertEqual(self.S.entries[0][0].i, 0)
        self.assertEqual(self.S.entries[0][1].i, 2)
        self.assertEqual(self.S.entries[0][2].i, 3)
