#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from functools import wraps
from multiprocessing import Pool
from time import time
from timeit import default_timer

from tqdm import tqdm


def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return test_f.read(2) == b'\x1f\x8b'


def multi_proc(processor, items, nr_cpus=2):
    """
    wrapper for multicore processing with progress bar
    """
    pool = Pool(nr_cpus)

    # if the number of items is explicit:
    try:
        total = len(items)
    except TypeError:
        total = None

    # loop through the items
    for _ in tqdm(
            pool.imap_unordered(processor, items),
            total=total
    ):
        pass


def time_it(func):
    """
    decorator for printing the execution time of a function call
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = default_timer()
        result = func(*args, **kwargs)
        end = default_timer()
        print("{} ran in {}s".format(func.__name__, round(end - start, 2)))
        return result
    return wrapper


class Progress(object):
    """
    Class for showing progress in for-loops
    (1) .init before loop
    (2) .update every loop
    (3) .finalize after loop
    optional parameters for initialization:
    - length of loop (will calculate approximate ETA)
    - refresh rate (default: every 100 items)
    """
    def __init__(self, length=None, rate=100):
        self.c = 0
        self.rate = rate
        when = time()
        self.start_glob = when
        self.avg_glob = 0
        self.start_rate = when
        self.avg_rate = 0
        self.d = length
        self.eta = 0

    # aliases
    def up(self):
        self.update()

    def fine(self):
        self.finalize()

    # methods
    def update(self):
        self.c += 1

        if self.c % self.rate == 0:
            when = time()
            self.avg_glob = (when-self.start_glob)/self.c
            self.bundle_rate = (when-self.start_rate)
            self.start_rate = when

            if self.d is not None:
                # calculate ETA
                self.eta = (self.d - self.c) * self.avg_glob
                msg = "%d%% (%d/%d). average: %s (%s last %d items). ETA: %s" % (
                    int(self.c/self.d*100),
                    self.c,
                    self.d,
                    int2str(self.avg_glob),
                    int2str(self.bundle_rate),
                    self.rate,
                    int2str(self.eta)
                )

            else:
                msg = "%d. average per %s item(s): %s. average last %s item(s): %s." % (
                    self.c,
                    self.rate,
                    int2str(self.avg_glob*100),
                    self.rate,
                    int2str(self.bundle_rate)
                )

            # print output
            trail = " ".join("" for _ in range(80-len(msg)))
            print(msg + trail, end="\r")

        if self.c == self.d:
            self.finalize()

    def finalize(self):
        total_time = time() - self.start_glob
        msg = "done. processed %d items in %s" % (self.c, int2str(total_time))
        trail = " ".join("" for _ in range(80-len(msg)))
        print(msg + trail)


# time conversion
def get_ymd():
    """ gets the current date in yyyymmdd-format """
    t = datetime.now()
    d = str(t.year) + '{:02d}'.format(t.month) + '{:02d}'.format(t.day)
    return d


def encow2unix(encow_time):
    # GMT = UTC
    dt = datetime.strptime(
        encow_time,
        '%a, %d %b %Y %H:%M:%S GMT'
    )
    # unix time = total seconds since 1970-01-01
    unix_time = int((dt - datetime(1970, 1, 1)).total_seconds())
    return unix_time


def twitter2unix(twitter_time):
    # twitter time always has 0000 offset (=UTC)
    dt = datetime.strptime(
        twitter_time,
        "%a %b %d %H:%M:%S +0000 %Y"
    )
    # unix time = total seconds since 1970-01-01
    unix_time = int((dt - datetime(1970, 1, 1)).total_seconds())
    return unix_time


def unix2ymd(unix_time):
    created_at = datetime.utcfromtimestamp(unix_time)
    return created_at.strftime('%Y%m%d')


def unix2ym(unix_time):
    created_at = datetime.utcfromtimestamp(unix_time)
    return created_at.strftime('%Y%m')


def unix2yw(unix_time):
    created_at = datetime.utcfromtimestamp(unix_time)
    year = created_at.isocalendar()[0]
    week = created_at.isocalendar()[1]
    return str(year) + "_week" + str(week)


def unix2ymd_hms(unix_time):
    created_at = datetime.utcfromtimestamp(unix_time)
    return created_at.strftime('%Y%m%d_%H%M%S')


# time formatting
def int2str(eta):
    """ returns an appropriately formatted str of the seconds provided """

    # miliseconds if less than 2 seconds
    if eta < 2:
        eta = 1000 * eta
        if eta >= 1:
            return "{:01} ms".format(int(eta))
        else:
            return "<1 ms"

    nr_days = int(eta // (60 * 60 * 24))
    nr_hours = int(eta // (60 * 60) % 24)

    # days and hours if more than a day
    if nr_days > 0:
        return "{:01} days, {:01} hours".format(nr_days, nr_hours)

    nr_minutes = int(eta // 60 % 60)
    # hours and minutes if more than 12 hours
    if nr_hours > 12:
        return "{:01} hours, {:01} minutes".format(nr_hours, nr_minutes)

    # fallback: hours, minutes, seconds
    nr_seconds = int(eta % 60)
    return "{:02}:{:02}:{:02}".format(nr_hours, nr_minutes, nr_seconds)
