#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import os
import xml
from collections import defaultdict

from vrt.utils import Progress, is_gz_file
from vrt.vrt import meta2dict


def create_file(path_in, corpus_name, registry_dir, data_dir, p_atts, s_atts, lemmatisation=False):
    """"""

    registry_file = os.path.join(registry_dir, corpus_name.lower())

    lines = [
        '#!/bin/bash',
        '',
        f'path_in="{path_in}"',
        f'corpus_name="{corpus_name}"',
        f'registry_file="{registry_file}"',
        f'data_dir="{data_dir}"',
        f'registry_dir="{registry_dir}"',
        '',
        'echo "create data directory"',
        'mkdir -p $data_dir',
        '',
        'echo "cwb-encode"',
        f'cwb-encode -d $data_dir -f $path_in -R "$registry_file" -xsB -c utf8 {p_atts} {s_atts}',
        '',
        'echo "cwb-make"',
        'cwb-make -r $registry_dir -M 4096 -V "$corpus_name"',
        ''
    ]

    if lemmatisation:

        # explicitly export p-att 'word' and 'lemma'
        p_atts = " ".join(["-P word", p_atts, "-P lemma"])
        # do not export s-att 'corpus'
        s_atts = s_atts.replace("-S corpus ", "")

        path_out = path_in.replace(".vrt.gz", "-lemma.vrt")
        if os.path.exists(path_out):
            raise FileExistsError(f'path for lemmatised corpus exists: {path_out}')

        lines += [
            'echo "lemmatisation"',
            'cwb-lemmatize-smor -E -T $corpus_name',
            '',
            'echo "export"',
            f'file_out="{path_out}"',
            f'cwb-decode -Cx $corpus_name {p_atts} {s_atts} > $file_out',
            '',
            'echo "compressing"',
            'gzip $file_out',
            ''
        ]

    return "\n".join(lines)


def guess_attributes(path_in, cut_off, rate=100000):
    """"""

    print("guessing attributes ...")

    s_atts = defaultdict(set)
    nr_p_atts = 1
    nr_p_lines = 0
    nr_s_lines = 0

    f = gzip.open(path_in, "rt") if is_gz_file(path_in) else open(path_in, "rt")
    pb = Progress(length=cut_off, rate=rate) if cut_off > 0 else Progress(rate=rate)
    for line in f:

        if line.startswith("<?"):
            # xml declaration
            continue

        elif line.startswith("<") and not line.startswith("</"):
            # s-atts
            nr_s_lines += 1
            typ, ann = parse_s_att(line)
            s_atts[typ] = s_atts[typ].union(ann)

        else:
            # p-atts
            nr_p_lines += 1
            nr_p_atts = max(nr_p_atts, len(line.split("\t")))

        pb.up()
        if cut_off > 0 and pb.c >= cut_off:
            break

    if cut_off <= 0 or pb.c < pb.d:
        pb.fine()

    f.close()

    # post-process s-attributes
    s_atts_new = list()
    for s in s_atts.keys():
        if len(s_atts[s]) == 0:
            s_atts_new.append(s)
        else:
            new = s + ":0+" + "+".join(sorted(list(s_atts[s])))
            s_atts_new.append(new)

    print(f"... saw {nr_p_lines} p-attribute lines and {nr_s_lines} s-attribute lines")
    print(f"... guessed {nr_p_atts} p-attributes and {len(s_atts)} s-attributes")

    return {
        's_atts': s_atts_new,
        'nr_p_atts': nr_p_atts
    }


def parse_s_att(line):
    """"""
    row = line.rstrip()
    row = row.rstrip(">").lstrip("<")
    row = row.split(" ")
    typ = row[0]
    try:
        ann = set(meta2dict(line, level=typ).keys())
    except xml.etree.ElementTree.ParseError:
        print("error when parsing s-attribute:")
        print(line)
    return typ, ann


def main(args):
    """"""

    # path_in
    path_in = args.path_in
    dir_in = os.path.dirname(path_in)
    f_name = args.path_in.split("/")[-1].split(".")[0].lower()

    # path_out
    if args.path_out is None:
        path_out = os.path.join(dir_in, f_name + ".sh")
        if os.path.exists(path_out) and not args.force:
            raise FileExistsError("\n".join([
                f'{path_out} exists',
                "you can force to overwrite by using --force / -f",
                "or by directly specifying the path using --path_out / -o"
            ]))
    else:
        path_out = args.path_out

    # corpus_name
    corpus_name = f_name.upper() if args.name is None else args.name.upper()

    # data directory
    data_dir = os.path.join(args.data_dir, corpus_name.lower())

    # attributes
    atts = guess_attributes(path_in, args.cut_off)
    p_atts = "-P " + " -P ".join(args.p_atts[: atts['nr_p_atts'] - 1]) if atts['nr_p_atts'] > 1 else ""
    s_atts = "-S " + " -S ".join(atts['s_atts'])

    # create file contents
    file_contents = create_file(path_in, corpus_name, args.registry_dir, data_dir, p_atts, s_atts, args.lemmatisation)

    # write
    with open(path_out, "wt") as f:
        f.write(file_contents)

    # status
    print(f"output written to {path_out}")
