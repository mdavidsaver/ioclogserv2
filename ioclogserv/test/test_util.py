# -*- coding: utf-8 -*-

from twisted.trial import unittest
from ioclogserv.util import rotateFile

from . import testutil

class TestRotate(unittest.TestCase, testutil.FileTest):

    def test_rotate(self):
        self.removeFile('rotate_test_file')
        self.removeFile('rotate_test_file.0')

        with open('rotate_test_file', 'w') as F:
            F.write('test1')

        self.assertFileMatch('rotate_test_file', 'test1')
        self.assertFileNotExist('rotate_test_file.0')

        # maxsize is large than file size
        rotateFile('rotate_test_file', nbackup=2, maxsize=300)

        self.assertFileMatch('rotate_test_file', 'test1')
        self.assertFileNotExist('rotate_test_file.0')

        rotateFile('rotate_test_file', nbackup=2, maxsize=3)

        self.assertFileNotExist('rotate_test_file')
        self.assertFileMatch('rotate_test_file.0', 'test1')

        with open('rotate_test_file', 'w') as F:
            F.write('test2')

        rotateFile('rotate_test_file', nbackup=2, maxsize=3)

        self.assertFileNotExist('rotate_test_file')
        self.assertFileMatch('rotate_test_file.0', 'test2')
        self.assertFileMatch('rotate_test_file.1', 'test1')

        with open('rotate_test_file', 'w') as F:
            F.write('test3')

        rotateFile('rotate_test_file', nbackup=2, maxsize=3)

        self.assertFileNotExist('rotate_test_file')
        self.assertFileMatch('rotate_test_file.0', 'test3')
        self.assertFileMatch('rotate_test_file.1', 'test2')

    def test_gap(self):
        self.removeFile('rotate_test_file')
        self.removeFile('rotate_test_file.0')
        self.removeFile('rotate_test_file.1')

        with open('rotate_test_file', 'w') as F:
            F.write('testa')
        with open('rotate_test_file.1', 'w') as F:
            F.write('testb')

        rotateFile('rotate_test_file', nbackup=2, maxsize=3)

        self.assertFileNotExist('rotate_test_file')
        self.assertFileMatch('rotate_test_file.0', 'testa')
        self.assertFileMatch('rotate_test_file.1', 'testb')
