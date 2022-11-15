#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import xml
import xml.etree.ElementTree as ET
from collections import defaultdict

from vrt.utils import Progress, is_gz_file, save_id, save_path_out
from vrt.vrt import dict2meta, force_categorical, meta2dict


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


def read_xml(path):
    """TODO"""
    with gzip.open(path, "rt") as f:
        root = ET.fromstring(f.read())
        for child in root:
            print(child.tag, child.attrib)


def check_file(path, cut_off=-1):
    """TODO"""
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


def process_path(path_in, path_out, force, level, id_key, categorical):

    f_name, path_out = save_path_out(path_in, path_out, suffix='-cqpweb.vrt.gz', force=force)
    ids = set()
    categorical_values = defaultdict(set)
    with gzip.open(path_in, "rt") as f, gzip.open(path_out, "wt") as f_out:

        text_count = 0

        pb = Progress(rate=1)
        for line in f:

            if line.startswith(f"<{level}") or line.startswith(f"<{level}>"):
                meta = meta2dict(line, level=level)
                id_encountered = force_categorical(meta.pop(id_key))
                id = save_id(id_encountered, ids)
                meta['id'] = id
                ids.add(id)
                for c in categorical:
                    key = force_categorical(c)
                    value = force_categorical(meta.pop(c))
                    meta[key] = value
                    categorical_values[key].add(value)
                line = dict2meta(meta)
            elif line.startswith(f"</{level}>"):
                line = "</text>" + "\n"
                text_count += 1
                pb.up()

            f_out.write(line)
        pb.fine()

    for key, values in categorical_values.items():
        print(f"- {key}: {len(values)} types")


def main(args):
    """"""

    process_path(args.path_in,
                 args.path_out,
                 args.force,
                 args.level,
                 args.id_key,
                 args.categorical)
