# -*- coding: utf-8 -*-

import os, os.path
import re, errno

class FileTest(object):
    def assertFileMatch(self, fname, pat, mode='r', flags=0, _inv=False):
        R = re.compile(pat)
        try:
            with open(fname, mode) as F:
                match=False
                for L in F.readlines():
                    M=R.match(L, flags)
                    if M is not None:
                        match=True
                        break
                if not _inv and not match:
                    raise self.failureException('File "%s" did not contain "%s"'%(fname,pat))
                if _inv and match:
                    raise self.failureException('File "%s" contains "%s"'%(fname,pat))
        except OSError as e:
            if e.errno==errno.ENOENT:
                raise self.failureException('File "%s" does not exist'%fname)
    def assertFileNotMatch(self, fname, pat, mode='r', flags=0, _inv=True):
        self.assertFileMatch(fname,  pat, mode, flags, _inv)

    def assertFileExist(self, fname):
        self.assertTrue(os.path.isfile(fname), 'File "%s" does not exist'%fname)
    def assertFileNotExist(self, fname):
        self.assertFalse(os.path.exists(fname), 'File "%s" exists'%fname)

    def removeFile(self, fname):
        try:
            os.remove(fname)
        except OSError as e:
            if e.errno!=errno.ENOENT:
                raise
        self.assertFileNotExist(fname)
