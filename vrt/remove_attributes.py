#!/usr/bin/python3
# -*- coding: utf-8 -*-

from vrt.utils import save_path_out, is_gz_file
from vrt.indexing import parse_s_att
import gzip


def process_path(path_in, path_out, force, p_atts, s_atts):

    f_name, path_out = save_path_out(path_in, path_out, suffix='.sh', force=force)

    f_in = gzip.open(path_in, "rt") if is_gz_file(path_in) else open(path_in, "rt")
    with gzip.open(path_out, "wt") as f_out:
        for line in f_in:

            # remove s-attribute
            typ = None
            if line.startswith("</"):
                typ = line.strip().strip("<>/")
            elif line.startswith("<"):
                typ, ann = parse_s_att(line)

            if typ in s_atts:
                continue

            f_out.write(line)

    f_in.close()


def main(args):
    """"""

    process_path(args.path_in,
                 args.path_out,
                 args.force,
                 args.p_atts,
                 args.s_atts)


path_in = "/home/ausgerechnet/repositories/leak-tool/backend/tests/data/raw/fiktives-urteil.vrt"
path_out = "/home/ausgerechnet/repositories/leak-tool/backend/tests/data/raw/fiktives-urteil-no-segments.vrt.gz"

process_path(path_in, path_out, True, p_atts=[], s_atts=['s', 'p'])
