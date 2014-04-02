# -*- coding: utf-8 -*-

import os, os.path
import re, errno

class FileTest(object):
    def assertFileMatch(self, fname, pat, mode='r', flags=0):
        R = re.compile(pat)
        try:
            with open(fname, mode) as F:
                if flags&re.MULTILINE:
                    M=R.match(F.read(), flags)
                    if M is None:
                        self.fail('File "%s" didn\'t contain "%s"'%(fname,pat))
                else:
                    match=False
                    for L in F.readlines():
                        M=R.match(L, flags)
                        if M is not None:
                            match=True
                            break
                    self.assertTrue(match, 'File "%s" did not contain "%s"'%(fname,pat))
        except OSError as e:
            if e.errno==errno.ENOENT:
                self.fail('File "%s" does not exist'%fname)

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
