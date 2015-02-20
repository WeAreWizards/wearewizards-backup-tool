#!/usr/bin/env python

import re
import argparse
import datetime
import subprocess

# Parse the following
# | 20150220150154 | complete | progress[webserver,/dev/xvda1,snap-8c1b0d7c] = 100% |
STATUS_RE = re.compile(' (\d{14}) \|\s+([a-z]+)\s+\|\s+[a-z]+\[([a-z-_]+)')



def get_backups(system, statefile=None):
    cmd = ['nixops', 'backup-status', '-d', system]
    if statefile:
        cmd = cmd + ['-s', statefile]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, _ = p.communicate()
    return out


def id_from_datetime(dt):
    return dt.strftime('%Y%m%d%H%M%S')

def parse_backups(s):
    for date, status, name in STATUS_RE.findall(s):
        dt = datetime.datetime(
            int(date[:4]),
            int(date[4:6]),
            int(date[6:8]),
            int(date[8:10]),
            int(date[10:12]),
            int(date[12:14])
        )
        yield dt, status, name


def whittle(dts, utcnow=None):
    """Takes a list of datetime.datetime instances and returns a whittled
    down list of the type:
    1) 1-per hour for last 24h
    2) 1-per day for last week
    3) weekly after
    """
    if utcnow is None:
        utcnow = datetime.datetime.utcnow()

    dts = sorted(list(dts), reverse=True) # newest first
    budget = 0
    total = 0
    # always keep the newest backup
    if dts:
        yield dts[0]

    for dt0, dt1 in zip(dts[1:], dts):
        delta = (dt1 - dt0).total_seconds()
        total += delta

        if total < 3600 * 24:
            cutoff = 3600
        elif total < 3600 * 24 * 7:
            cutoff = 3600 * 24
        else:
            cutoff = 3600 * 24 * 7

        budget += delta
        if budget > cutoff:
            yield dt1
            budget -= cutoff


def main():
    parser = argparse.ArgumentParser(
        description='Run nixops backups and garbage-collect old state.')
    parser.add_argument(
        '--state', type=str, default=None,
        help='Statefile to use for nixops')
    parser.add_argument(
        'systems', metavar='SYSTEMS', type=str, nargs='+',
        help='Name of the systems, e.g. wearewizards.io')

    args = parser.parse_args()

    for s in args.systems:
        backups = parse_backups(get_backups(s, args.state))
        backup_ids = set(x[0] for x in backups)
        keep = set(whittle(backup_ids))
        remove = backup_ids - keep

        for x in remove:
            backup_id = id_from_datetime(x)
            cmd = ['nixops', 'remove-backup', '-d', s, backup_id]
            if args.state:
                cmd = cmd + ['-s', args.state]
            subprocess.check_output(cmd)


if __name__ == '__main__':
    main()
