#! /usr/bin/env python
# -*- coding: utf-8 -*-

from vrt.utils import save_path_out, is_gz_file, Progress
from vrt.meta import meta2dict
import xml
import gzip
from collections import defaultdict


def parse_s_att(line):
    """"""
    row = line.rstrip()
    row = row.rstrip(">").lstrip("<")
    row = row.split(" ")
    typ = row[0]
    try:
        ann = meta2dict(line, level=typ)
    except xml.etree.ElementTree.ParseError:
        print("error when parsing s-attribute:")
        print(line)
    return typ, ann


def check_file(path, cut_off=-1):

    # <text id="">, count
    values = defaultdict(set)
    nr_p_atts = 1
    nr_p_lines = 0
    nr_s_lines = 0

    f = gzip.open(path, "rt") if is_gz_file(path) else open(path, "rt")
    pb = Progress(length=cut_off, rate=10000) if cut_off > 0 else Progress(rate=10000)
    for line in f:

        if line.startswith("<?"):
            # xml declaration
            continue

        elif line.startswith("</"):
            pass

        elif line.startswith("<"):
            # s-atts
            nr_s_lines += 1
            typ, ann = parse_s_att(line)
            for a in ann.keys():
                values["-".join([typ, a])].add(ann[a])

        else:
            # p-atts
            # TODO check if XML escaped
            nr_p_lines += 1
            nr_p_atts = max(nr_p_atts, len(line.split("\t")))

        pb.up()
        if cut_off > 0 and pb.c >= cut_off:
            break

    if cut_off <= 0 or pb.c < pb.d:
        pb.fine()

    f.close()

    for k, v in values.items():
        print(k, len(v))

    # meta data types


def modify_file(rename=dict(), ):
    pass


def process_path(path_in, path_out, force):

    check_file(path_in)

    f_name, path_out = save_path_out(path_in, path_out, suffix='-cqpweb.vrt.gz', force=force)


def main(args):
    """"""

    process_path(args.path_in, args.path_out, args.force, args.name,
                 args.p_atts, args.cut_off, args.data_dir, args.registry_dir,
                 args.lemmatisation)
