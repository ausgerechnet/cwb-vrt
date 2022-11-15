#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
from functools import wraps
from multiprocessing import Pool
from time import time
from timeit import default_timer

from tqdm import tqdm


def update_id(id):
    hit = re.search(r"(.*)__(\d+)$", str(id))
    if hit:
        prefix = hit.group(1)
        nr = int(hit.group(2))
        id_new = prefix + "__" + str(nr + 1)
    else:
        id_new = str(id) + '__1'
    return id_new


def save_id(id, ids):
    id_old = id
    while id in ids:
        id = update_id(id)
    if id_old != id:
        print(f"\nduplicate id: {id_old} → {id}")
    return id


def save_path_out(path_in, path_out, suffix='.sh', force=False):

    dir_in = os.path.dirname(path_in)
    f_name = path_in.split("/")[-1].split(".")[0].lower()

    if path_out is None:
        path_out = os.path.join(dir_in, f_name + suffix)
        if os.path.exists(path_out):
            if force:
                print(f'warning: file "{path_out}" exists -- forced overwrite mode')
            else:
                raise FileExistsError("\n".join([
                    f'error: file "{path_out}" already exists',
                    "you can force overwrite by using --force or by specifying a --path_out"
                ]))

    return f_name, path_out


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


class Progress:
    """
    Class for showing progress in for-loops
    (1) .init before loop
    (2) .update every loop
    (3) .finalize after loop
    """
    def __init__(self, length=None, rate=1):
        """
        optional parameters for initialization:
        - length of loop (will calculate approximate ETA)
        - refresh rate (default: every 100 items)
        """
        when = time()
        self.start_glob = when  # start time of the progress bar
        self.length = length    # total number of items

        self.rate = rate        # number of seconds after which to refresh

        self.c = 0              # number of items encountered

        self.c_count = self.c   # start counter of this bundle
        self.c_time = time()    # start time of this bundle

    # aliases
    def up(self):
        self.update()

    def fine(self):
        self.finalize()

    # methods
    def update(self):

        self.c += 1
        when = time()

        current_time = when - self.c_time
        current_size = self.c - self.c_count

        if current_time > self.rate:

            avg_glob = (when-self.start_glob) / self.c

            if self.length is not None:
                # calculate ETA
                eta = (self.length - self.c) * avg_glob
                msg = " ".join([
                    f"{int(self.c/self.length*100)}% ({self.c}/{self.length}).",
                    f"average: {int2str(avg_glob)}.",
                    f"average last {current_size} item(s): {int2str(current_time/current_size)}.",
                    f"ETA: {int2str(eta)}"
                ])

            else:
                msg = " ".join([
                    f"{self.c}.",
                    f"average: {int2str(avg_glob)}.",
                    f"average last {current_size} item(s): {int2str(current_time/current_size)}."
                ])

            # print output
            trail = " ".join("" for _ in range(100-len(msg)))
            print(msg + trail, end="\r")

            # update
            self.c_time = time()
            self.c_count = self.c

        if self.c == self.length:
            self.finalize()

    def finalize(self):
        total_time = time() - self.start_glob
        msg = "done. processed %d items in %s" % (self.c, int2str(total_time))
        trail = " ".join("" for _ in range(100-len(msg)))
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
    unix_time = int((dt - datetime(1970, 1, 1)).total_seconds())
    return unix_time


def twitter2unix(twitter_time):
    # twitter time always has 0000 offset (=UTC)
    dt = datetime.strptime(
        twitter_time,
        "%a %b %d %H:%M:%S +0000 %Y"
    )
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
