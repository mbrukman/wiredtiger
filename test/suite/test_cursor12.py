#!/usr/bin/env python
#
# Public Domain 2014-2017 MongoDB, Inc.
# Public Domain 2008-2014 WiredTiger, Inc.
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import random, string
import wiredtiger, wttest
from helper import copy_wiredtiger_home
from wtdataset import SimpleDataSet
from wtscenario import make_scenarios

# test_cursor12.py
#    Test cursor modify call
class test_cursor12(wttest.WiredTigerTestCase):
    keyfmt = [
        ('recno', dict(keyfmt='r')),
        ('string', dict(keyfmt='S')),
    ]
    types = [
        ('file', dict(uri='file:modify')),
        ('lsm', dict(uri='lsm:modify')),
        ('table', dict(uri='table:modify')),
    ]
    scenarios = make_scenarios(types, keyfmt)

    # List with original value, final value, and modifications to get
    # there.
    list = [
    {
    'o' : 'ABCDEFGH',           # no operation
    'f' : 'ABCDEFGH',
    'mods' : [['', 0, 0]]
    },{
    'o' : 'ABCDEFGH',           # no operation with offset
    'f' : 'ABCDEFGH',
    'mods' : [['', 4, 0]]
    },{
    'o' : 'ABCDEFGH',           # rewrite beginning
    'f' : '--CDEFGH',
    'mods' : [['--', 0, 2]]
    },{
    'o' : 'ABCDEFGH',           # rewrite end
    'f' : 'ABCDEF--',
    'mods' : [['--', 6, 2]]
    },{
    'o' : 'ABCDEFGH',           # append
    'f' : 'ABCDEFGH--',
    'mods' : [['--', 8, 2]]
    },{
    'o' : 'ABCDEFGH',           # append with gap
    'f' : 'ABCDEFGH\00\00--',
    'mods' : [['--', 10, 2]]
    },{
    'o' : 'ABCDEFGH',           # multiple replacements
    'f' : 'A-C-E-G-',
    'mods' : [['-', 1, 1], ['-', 3, 1], ['-', 5, 1], ['-', 7, 1]]
    },{
    'o' : 'ABCDEFGH',           # multiple overlapping replacements
    'f' : 'A-CDEFGH',
    'mods' : [['+', 1, 1], ['+', 1, 1], ['+', 1, 1], ['-', 1, 1]]
    },{
    'o' : 'ABCDEFGH',           # multiple overlapping gap replacements
    'f' : 'ABCDEFGH\00\00--',
    'mods' : [['+', 10, 1], ['+', 10, 1], ['+', 10, 1], ['--', 10, 2]]
    },{
    'o' : 'ABCDEFGH',           # shrink beginning
    'f' : '--EFGH',
    'mods' : [['--', 0, 4]]
    },{
    'o' : 'ABCDEFGH',           # shrink middle
    'f' : 'AB--GH',
    'mods' : [['--', 2, 4]]
    },{
    'o' : 'ABCDEFGH',           # shrink end
    'f' : 'ABCD--',
    'mods' : [['--', 4, 4]]
    },{
    'o' : 'ABCDEFGH',           # grow beginning
    'f' : '--ABCDEFGH',
    'mods' : [['--', 0, 0]]
    },{
    'o' : 'ABCDEFGH',           # grow middle
    'f' : 'ABCD--EFGH',
    'mods' : [['--', 4, 0]]
    },{
    'o' : 'ABCDEFGH',           # grow end
    'f' : 'ABCDEFGH--',
    'mods' : [['--', 8, 0]]
    },{
    'o' : 'ABCDEFGH',           # discard beginning
    'f' : 'EFGH',
    'mods' : [['', 0, 4]]
    },{
    'o' : 'ABCDEFGH',           # discard middle
    'f' : 'ABGH',
    'mods' : [['', 2, 4]]
    },{
    'o' : 'ABCDEFGH',           # discard end
    'f' : 'ABCD',
    'mods' : [['', 4, 4]]
    },{
    'o' : 'ABCDEFGH',           # discard everything
    'f' : '',
    'mods' : [['', 0, 8]]
    },{
    'o' : 'ABCDEFGH',           # overlap the end and append
    'f' : 'ABCDEF--XX',
    'mods' : [['--XX', 6, 2]]
    },{
    'o' : 'ABCDEFGH',           # overlap the end with incorrect size
    'f' : 'ABCDEFG01234567',
    'mods' : [['01234567', 7, 2000]]
    },{                         # many updates
    'o' : '-ABCDEFGHIJKLMNOPQRSTUVWXYZ-',
    'f' : '-eeeeeeeeeeeeeeeeeeeeeeeeee-',
    'mods' : [['a', 1,  1], ['a', 2,  1], ['a', 3,  1], ['a', 4,  1],
              ['a', 5,  1], ['a', 6,  1], ['a', 7,  1], ['a', 8,  1],
              ['a', 9,  1], ['a', 10, 1], ['a', 11, 1], ['a', 12, 1],
              ['a', 13, 1], ['a', 14, 1], ['a', 15, 1], ['a', 16, 1],
              ['a', 17, 1], ['a', 18, 1], ['a', 19, 1], ['a', 20, 1],
              ['a', 21, 1], ['a', 22, 1], ['a', 23, 1], ['a', 24, 1],
              ['a', 25, 1], ['a', 26, 1],
              ['b', 1,  1], ['b', 2,  1], ['b', 3,  1], ['b', 4,  1],
              ['b', 5,  1], ['b', 6,  1], ['b', 7,  1], ['b', 8,  1],
              ['b', 9,  1], ['b', 10, 1], ['b', 11, 1], ['b', 12, 1],
              ['b', 13, 1], ['b', 14, 1], ['b', 15, 1], ['b', 16, 1],
              ['b', 17, 1], ['b', 18, 1], ['b', 19, 1], ['b', 20, 1],
              ['b', 21, 1], ['b', 22, 1], ['b', 23, 1], ['b', 24, 1],
              ['b', 25, 1], ['b', 26, 1],
              ['c', 1,  1], ['c', 2,  1], ['c', 3,  1], ['c', 4,  1],
              ['c', 5,  1], ['c', 6,  1], ['c', 7,  1], ['c', 8,  1],
              ['c', 9,  1], ['c', 10, 1], ['c', 11, 1], ['c', 12, 1],
              ['c', 13, 1], ['c', 14, 1], ['c', 15, 1], ['c', 16, 1],
              ['c', 17, 1], ['c', 18, 1], ['c', 19, 1], ['c', 20, 1],
              ['c', 21, 1], ['c', 22, 1], ['c', 23, 1], ['c', 24, 1],
              ['c', 25, 1], ['c', 26, 1],
              ['d', 1,  1], ['d', 2,  1], ['d', 3,  1], ['d', 4,  1],
              ['d', 5,  1], ['d', 6,  1], ['d', 7,  1], ['d', 8,  1],
              ['d', 9,  1], ['d', 10, 1], ['d', 11, 1], ['d', 12, 1],
              ['d', 13, 1], ['d', 14, 1], ['d', 15, 1], ['d', 16, 1],
              ['d', 17, 1], ['d', 18, 1], ['d', 19, 1], ['d', 20, 1],
              ['d', 21, 1], ['d', 22, 1], ['d', 23, 1], ['d', 24, 1],
              ['d', 25, 1], ['d', 26, 1],
              ['e', 1,  1], ['e', 2,  1], ['e', 3,  1], ['e', 4,  1],
              ['e', 5,  1], ['e', 6,  1], ['e', 7,  1], ['e', 8,  1],
              ['e', 9,  1], ['e', 10, 1], ['e', 11, 1], ['e', 12, 1],
              ['e', 13, 1], ['e', 14, 1], ['e', 15, 1], ['e', 16, 1],
              ['e', 17, 1], ['e', 18, 1], ['e', 19, 1], ['e', 20, 1],
              ['e', 21, 1], ['e', 22, 1], ['e', 23, 1], ['e', 24, 1],
              ['e', 25, 1], ['e', 26, 1]]
    }
    ]

    # Skip record number keys with LSM.
    def skip(self):
        return self.keyfmt == 'r' and 'lsm' in self.uri

    # Create a set of modified records and verify in-memory reads.
    def modify_load(self, ds, single):
        # For each test in the list:
        #       set the original value,
        #       apply modifications in order,
        #       confirm the final state
        row = 10
        c = self.session.open_cursor(self.uri, None)
        for i in self.list:
            c.set_key(ds.key(row))
            c.set_value(i['o'])
            self.assertEquals(c.update(), 0)
            c.reset()

            c.set_key(ds.key(row))
            mods = []
            for j in i['mods']:
                mod = wiredtiger.Modify(j[0], j[1], j[2])
                mods.append(mod)
            self.assertEquals(c.modify(mods), 0)
            c.reset()

            c.set_key(ds.key(row))
            self.assertEquals(c.search(), 0)
            self.assertEquals(c.get_value(), i['f'])

            if not single:
                row = row + 1
        c.close()

    # Confirm the modified records are correct.
    def modify_confirm(self, ds, single):
        # For each test in the list:
        #       confirm the final state is there.
        row = 10
        c = self.session.open_cursor(self.uri, None)
        for i in self.list:
            c.set_key(ds.key(row))
            self.assertEquals(c.search(), 0)
            self.assertEquals(c.get_value(), i['f'])

            if not single:
                row = row + 1
        c.close()

    # Smoke-test the modify API, operating on a group of records.
    def test_modify_smoke(self):
        if self.skip():
            return

        ds = SimpleDataSet(self,
            self.uri, 100, key_format=self.keyfmt, value_format='u')
        ds.populate()
        self.modify_load(ds, False)

    # Smoke-test the modify API, operating on a single record
    def test_modify_smoke_single(self):
        if self.skip():
            return

        ds = SimpleDataSet(self,
            self.uri, 100, key_format=self.keyfmt, value_format='u')
        ds.populate()
        self.modify_load(ds, True)

    # Smoke-test the modify API, closing and re-opening the database.
    def test_modify_smoke_reopen(self):
        if self.skip():
            return

        ds = SimpleDataSet(self,
            self.uri, 100, key_format=self.keyfmt, value_format='u')
        ds.populate()
        self.modify_load(ds, False)

        # Flush to disk, forcing reconciliation.
        self.reopen_conn()

        self.modify_confirm(ds, False)

    # Smoke-test the modify API, recovering the database.
    def test_modify_smoke_recover(self):
        if self.skip():
            return

        # Close the original database.
        self.conn.close()

        # Open a new database with logging configured.
        self.conn_config = \
            'log=(enabled=true),transaction_sync=(method=dsync,enabled)'
        self.conn = self.setUpConnectionOpen(".")
        self.session = self.setUpSessionOpen(self.conn)

        # Populate a database, and checkpoint it so it exists after recovery.
        ds = SimpleDataSet(self,
            self.uri, 100, key_format=self.keyfmt, value_format='u')
        ds.populate()
        self.session.checkpoint()
        self.modify_load(ds, False)

        # Crash and recover in a new directory.
        newdir = 'RESTART'
        copy_wiredtiger_home('.', newdir)
        self.conn.close()
        self.conn = self.setUpConnectionOpen(newdir)
        self.session = self.setUpSessionOpen(self.conn)
        self.session.verify(self.uri)

        self.modify_confirm(ds, False)

    # Check that we can perform a large number of modifications to a record.
    def test_modify_many(self):
        ds = SimpleDataSet(self,
            self.uri, 20, key_format=self.keyfmt, value_format='u')
        ds.populate()

        c = self.session.open_cursor(self.uri, None)
        c.set_key(ds.key(10))
        orig = 'abcdefghijklmnopqrstuvwxyz'
        c.set_value(orig)
        self.assertEquals(c.update(), 0)
        for i in range(0, 50000):
            new = "".join([random.choice(string.digits) for i in xrange(5)])
            orig = orig[:10] + new + orig[15:]
            mods = []
            mod = wiredtiger.Modify(new, 10, 5)
            mods.append(mod)
            self.assertEquals(c.modify(mods), 0)

        c.set_key(ds.key(10))
        self.assertEquals(c.search(), 0)
        self.assertEquals(c.get_value(), orig)

    # Check that modify returns not-found after a delete.
    def test_modify_delete(self):
        ds = SimpleDataSet(self,
            self.uri, 20, key_format=self.keyfmt, value_format='u')
        ds.populate()

        c = self.session.open_cursor(self.uri, None)
        c.set_key(ds.key(10))
        self.assertEquals(c.remove(), 0)

        mods = []
        mod = wiredtiger.Modify('ABCD', 3, 3)
        mods.append(mod)

        c.set_key(ds.key(10))
        self.assertEqual(c.modify(mods), wiredtiger.WT_NOTFOUND)

if __name__ == '__main__':
    wttest.run()
