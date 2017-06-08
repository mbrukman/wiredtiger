#!/usr/bin/env python
#
# Public Domain 2014-2016 MongoDB, Inc.
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
#
# test_compat01.py
# Check compatibility API
#

import fnmatch, os, shutil, sys, time
from suite_subprocess import suite_subprocess
from wtscenario import make_scenarios
import wttest

class test_compat01(wttest.WiredTigerTestCase, suite_subprocess):
    # Add enough entries and use a small log size to generate more than
    # one log file.
    entries = 2000
    logmax = "100K"
    tablename = 'test_compat01'
    uri = 'table:' + tablename
    sync_list = [
        '(method=fsync,enabled)',
        '(method=none,enabled)',
    ]

    # The API uses only the major and minor numbers but accepts with
    # and without the patch number.  Test both.
    start_compat = [
        ('def', dict(compat1='none', current1=True)),
        ('current', dict(compat1="3.0", current1=True)),
        ('current_patch', dict(compat1="3.0.0", current1=True)),
        ('minor_only', dict(compat1="2.6", current1=False)),
        ('minor_patch', dict(compat1="2.6.1", current1=False)),
        ('old', dict(compat1="1.8", current1=False)),
        ('old_patch', dict(compat1="1.8.1", current1=False)),
    ]
    restart_compat = [
        ('def', dict(compat2='none', current2=True)),
        ('current', dict(compat2="3.0", current2=True)),
        ('current_patch', dict(compat2="3.0.0", current2=True)),
        ('minor_only', dict(compat2="2.6", current2=False)),
        ('minor_patch', dict(compat2="2.6.1", current2=False)),
        ('old', dict(compat2="1.8", current2=False)),
        ('old_patch', dict(compat2="1.8.1", current2=False)),
    ]
    scenarios = make_scenarios(restart_compat, start_compat)

    def make_compat_str(self, create):
        compat_str = ''
        if (create == True and self.compat1 != 'none'):
            #compat_str = 'verbose=(temporary),compatibility=(release="%s"),' % self.compat1
            compat_str = 'compatibility=(release="%s"),' % self.compat1
        elif (create == False and self.compat2 != 'none'):
            #compat_str = 'verbose=(temporary),compatibility=(release="%s"),' % self.compat2
            compat_str = 'compatibility=(release="%s"),' % self.compat2
        return compat_str

    def conn_config(self):
        # Cycle through the different transaction_sync values in a
        # deterministic manner.
        txn_sync = self.sync_list[
            self.scenario_number % len(self.sync_list)]
        # Set archive false on the home directory.
        log_str = 'log=(archive=false,enabled,file_max=%s),' % self.logmax + \
            'transaction_sync="%s",' % txn_sync
        compat_str = self.make_compat_str(True)
        self.pr("Conn config:" + log_str + compat_str)
        return log_str + compat_str

    def check_prev_lsn(self, exists, conn_close):
        #
        # Run printlog and look for the prev_lsn log record.  Verify its
        # existence with the passed in expected result.  We don't use
        # check_file_contains because that only looks in the first 100K and
        # we don't know how big our text-based log output is.  Look through
        # the entire file if needed and set a boolean for comparison.
        #
        self.runWt(['printlog'], outfilename='printlog.out', closeconn=conn_close)
        contains = False
        with open('printlog.out') as logfile:
            for line in logfile:
                if 'prev_lsn' in line:
                    contains = True
                    break
        self.assertEqual(exists, contains)

    def check_log(self, reconfig):
        orig_logs = fnmatch.filter(os.listdir('.'), "*Log*")
        compat_str = self.make_compat_str(False)
        if not reconfig:
            #
            # Close and open the connection to force recovery and log archiving
            # even if archive is turned off (in some circumstances).
            # If we are downgrading we must archive newer logs.  Verify
            # log files have or have not been archived.
            #
            self.check_prev_lsn(self.current1, True)

            self.conn.close()
            log_str = 'log=(enabled,file_max=%s,archive=false),' % self.logmax
            restart_config = log_str + compat_str
            self.pr("Restart conn " + restart_config)
            #
            # Open a connection to force it to run recovery.
            #
            conn = self.wiredtiger_open('.', restart_config)
            conn.close()
            check_close = False
        else:
            self.pr("Reconfigure: " + compat_str)
            self.conn.reconfigure(compat_str)
            check_close = True

        #
        # Archiving is turned off explicitly.
        #
        # Check logs. The original logs should have been archived only if
        # we downgraded.  In all other cases the original logs should be there.
        #
        cur_logs = fnmatch.filter(os.listdir('.'), "*Log*")
        log_present = True
        #if self.current1 == True and self.current2 == False:
        #    log_present = False
        for o in orig_logs:
            self.assertEqual(log_present, o in cur_logs)

        # Run printlog and verify the new record does or does not exist.
        #self.check_prev_lsn(self.current2, check_close)

    def run_test(self, reconfig):
        # If reconfiguring with the empty string there is nothing to do.
        if reconfig == True and self.compat2 == 'none':
            return
        self.session.create(self.uri, 'key_format=i,value_format=i')
        c = self.session.open_cursor(self.uri, None)
        #
        # Add some entries to generate log files.
        #
        for i in range(self.entries):
            c[i] = i + 1
        c.close()

        # Check the log state after the entire op completes
        # and run recovery with the restart compatibility mode.
        self.check_log(reconfig)
        c = self.session.open_cursor(self.uri, None)
        #
        # Add some entries to generate log files.
        #
        for i in range(20):
            c[i+1000000] = i + 1000000
        c.close()

    # Run the same test but reset the compatibility via
    # reconfigure or changing it when reopening the connection.
    def test_reconfig(self):
        self.run_test(True)

    def test_restart(self):
        self.run_test(False)

if __name__ == '__main__':
    wttest.run()
