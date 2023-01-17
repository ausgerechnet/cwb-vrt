#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import errno
import gzip
import os
import re
import sys
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
        print(f"\nduplicate id: {id_old} → {id}", file=sys.stderr)
    return id


def save_path_out(path_in, path_out, suffix='.sh', force=False, dir_out=None):

    dir_in = os.path.dirname(path_in)
    f_name = path_in.split("/")[-1].split(".")[0].lower()

    if path_out is None:

        if dir_out is None:
            dir_out = dir_in

        path_out = os.path.join(dir_out, f_name + suffix)

    if os.path.exists(path_out):
        if force:
            print(f'warning: file "{path_out}" exists -- forced overwrite mode', file=sys.stderr)
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
    """Class for showing progress in for-loops
    (1) pb = Progress() before loop
    (2) pb.update()     every loop
    (3) pb.finalize()   after loop
    """

    def __init__(self, length=None, rate=1):
        """
        :param int length: length of loop (will calculate approximate ETA)
        :param int rate: refresh rate (default: every second)
        """

        self.start_glob = time()  # start time of the progress bar
        self.length = length      # total number of items
        self.rate = rate          # refresh rate

        self.c = 0                    # number of items already encountered
        self.boundle_c = self.c       # start counter of this bundle
        self.boundle_time = time()    # start time of this bundle
        self.max_message = 0

    def up(self):
        """alias for self.update()"""
        self.update()

    def fine(self):
        """alias for self.finalize()"""
        self.finalize()

    def update(self):

        self.c += 1
        when = time()

        current_time = when - self.boundle_time
        current_size = self.c - self.boundle_c

        if current_time > self.rate:

            avg_glob = (when-self.start_glob) / self.c

            if self.length is not None:
                msg = " ".join([
                    f"{int(self.c/self.length*100)}% ({self.c}/{self.length}).",
                    f"average: {int2str(avg_glob)}.",
                    f"average last {current_size} item(s): {int2str(current_time/current_size)}.",
                    f"ETA: {int2str((self.length - self.c) * avg_glob)}"
                ])

            else:
                msg = " ".join([
                    f"{self.c}.",
                    f"average: {int2str(avg_glob)}.",
                    f"average last {current_size} item(s): {int2str(current_time/current_size)}.",
                    f"total time: {int2str(when-self.start_glob)}"
                ])

            # print output
            self.print_line(msg)

            # update bundle start counter and start time
            self.boundle_c = self.c
            self.boundle_time = when

        if self.c == self.length:
            self.finalize()

    def print_line(self, msg, end="\r", file=sys.stderr):
        self.max_message = max(self.max_message, len(msg) + 1)
        trail = " ".join("" for _ in range(self.max_message-len(msg)))
        print(msg + trail, end=end, file=file)

    def finalize(self):
        total_time = time() - self.start_glob
        msg = "done. processed %d items in %s" % (self.c, int2str(total_time))
        self.print_line(msg, "\n")


def unix2ymd_hms(unix_time):
    created_at = datetime.utcfromtimestamp(unix_time)
    return created_at.strftime('%Y%m%d_%H%M%S')


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


def int2str(seconds):
    """ returns an appropriately formatted str of the seconds provided """

    # very small
    if seconds < 2:
        milli_seconds = 1000 * seconds
        if milli_seconds > 2:
            return f"{int(milli_seconds)} ms"

        micro_seconds = 1000 * milli_seconds
        if micro_seconds > 2:
            return f"{int(micro_seconds)} µs"
        elif micro_seconds > .1:
            return f"{round(micro_seconds, 2)} µs"
        elif micro_seconds > .01:
            return f"{round(micro_seconds, 3)} µs"
        elif micro_seconds > .001:
            return f"{round(micro_seconds, 4)} µs"
        else:
            return "<1 ns"

    # days and hours if more than a day
    nr_days = int(seconds // (60 * 60 * 24))
    nr_hours = int(seconds // (60 * 60) % 24)
    if nr_days > 0:
        return f"{nr_days} days, {nr_hours} hours"

    # hours and minutes if more than 12 hours
    nr_minutes = int(seconds // 60 % 60)
    if nr_hours > 12:
        return f"{nr_hours} hours, {nr_minutes} minutes"

    # default: hours:minutes:seconds
    nr_seconds = int(seconds % 60)
    return "{:02}:{:02}:{:02}".format(nr_hours, nr_minutes, nr_seconds)


class MultiFileWriter:
    """write to multiple files at a time without specifing paths in
    advance.  takes care of appropriately opening and closing all file
    connections, respecting the upper limit of connections.

    do not forget to close files with mfw.close()
    TODO: implement as context manager

    """

    def __init__(self, compression='gzip', init_mode='wt', create_dir=True, limit=512):
        """

        :param int limit: upper limit of simultaneous connections (on Ubuntu: check with "ulimit -n" = 1024)
        """
        self.limit = limit
        self.init_mode = init_mode
        self.create_dir = create_dir
        self.compression = compression
        self.paths = dict()     # [path]: dict(open?, count, connection)
        self.nr_open = 0

    def _open(self, path, mode, warning=True):

        # close if no more space
        # TODO: add heuristics for closing rarely used connections instead of all
        if self.nr_open >= self.limit:
            if warning:
                print('\n' + 'too many open connections, closing all of them')
            self.close()

        # check if parent directories exist
        if self.create_dir:
            if not os.path.exists(os.path.dirname(path)):
                try:
                    os.makedirs(os.path.dirname(path))
                except OSError as exc:  # guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

        # open connection
        if self.compression == 'gzip':
            self.paths[path]['connection'] = gzip.open(path, mode=mode)
        elif self.compression is None:
            self.paths[path]['connection'] = open(path, mode=mode)
        self.paths[path]['open'] = True

        # increase count
        self.nr_open += 1

    def write(self, path, string):

        if path not in self.paths.keys():

            # init path
            self.paths[path] = dict()
            # open connection for first time
            self._open(path, self.init_mode)
            # start counting
            self.paths[path]['count'] = 0

        elif not self.paths[path]['open']:

            # re-open connection (attach to file)
            self._open(path, 'at')

        # write
        self.paths[path]['connection'].write(string)
        # count use
        self.paths[path]['count'] += 1

    def close(self):

        # close all paths
        for path in self.paths.keys():
            if 'connection' in self.paths[path].keys():
                self.paths[path]['connection'].close()
            self.paths[path]['open'] = False
        self.nr_open = 0
