import datetime
import unittest

import run_backups


TEST_INPUT = """
+----------------+----------+-----------------------------------------------------+
|   Backup ID    |  Status  |                         Info                        |
+----------------+----------+-----------------------------------------------------+
| 20150220150154 | complete |    progress[webserver,/dev/xvda1,snap-791f0e89] =   |
| 20150220114718 | complete | progress[webserver,/dev/xvda1,snap-ab382f5b] = 100% |
+----------------+----------+-----------------------------------------------------+
"""

TEST_TIMES = [
    datetime.datetime(2015, 2, 20, 15, 0, 0) - datetime.timedelta(minutes=59*i)
    for i in xrange(500)
]


class BackupTestCase(unittest.TestCase):

    def test_re(self):
        self.assertEquals(
            run_backups.STATUS_RE.findall(TEST_INPUT),
            [('20150220150154', 'complete', 'webserver'),
             ('20150220114718', 'complete', 'webserver')]
        )

    def test_parse(self):
        self.assertEquals(
            list(run_backups.parse_backups(TEST_INPUT)),
            [(datetime.datetime(2015, 2, 20, 15, 1, 54), 'complete', 'webserver'),
             (datetime.datetime(2015, 2, 20, 11, 47, 18), 'complete', 'webserver')]
        )

    def test_whittle(self):
        # Have ~500 hours == 24 + 6 + 1 items
        dts = list(run_backups.whittle(TEST_TIMES, datetime.datetime(2015, 2, 20, 15, 0, 0)))
        self.assertEquals(len(dts), 31)
        self.assertEquals(dts[0].hour, 15)
        self.assertEquals(dts[-1].day, 6)
