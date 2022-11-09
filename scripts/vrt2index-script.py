#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import os
import xml
from argparse import ArgumentParser
from collections import defaultdict

from cutils.times import Progress
from cutils.vrt import meta2dict


def create_file(path_in, corpus_name, registry_dir, data_dir, p_atts, s_atts, lemmatisation=False):

    # registry file
    registry_file = os.path.join(registry_dir, corpus_name.lower())

    lines = [
        '#!/bin/bash',
        '',
        f'file_in="{path_in}"',
        f'corpus_name="{corpus_name}"',
        f'registry_file="{registry_file}"',
        f'data_dir="{data_dir}"',
        f'export CORPUS_REGISTRY="{registry_dir}"',
        '',
        'echo "create data directory"',
        'mkdir -p $data_dir',
        '',
        'echo "cwb-encode"',
        f'cwb-encode -d $data_dir -f $file_in -R "$registry_file" -xsB -c utf8 {p_atts} {s_atts}',
        '',
        'echo "cwb-make on remaining attributes"',
        'cwb-make -M 4096 -V "$corpus_name"',
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


def main(args, registry_dir, data_dir):

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
    corpus_name = f_name.upper() if args.corpus_name is None else args.corpus_name.upper()

    # data directory
    data_dir = os.path.join(data_dir, corpus_name.lower())

    # attributes
    atts = guess_attributes(path_in, args.cut_off)
    p_atts = "-P " + " -P ".join(args.p_atts[: atts['nr_p_atts'] - 1]) if atts['nr_p_atts'] > 1 else ""
    s_atts = "-S " + " -S ".join(atts['s_atts'])

    # create file contents
    file_contents = create_file(path_in, corpus_name, registry_dir, data_dir, p_atts, s_atts, args.lemmatisation)

    # write
    with open(path_out, "wt") as f:
        f.write(file_contents)

    # status
    print(f"output written to {path_out}")


def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return test_f.read(2) == b'\x1f\x8b'


def guess_attributes(path_in, cut_off, rate=100000):

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

    if cut_off <= 0:
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


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("path_in",
                        type=str,
                        help="path to .vrt.gz to index")
    parser.add_argument("--p_atts",
                        "-p",
                        dest="p_atts",
                        nargs="+",
                        type=str,
                        default=['pos', 'lemma'],
                        help="what p-attributes to index")
    parser.add_argument("--path_out",
                        "-o",
                        dest="path_out",
                        default=None,
                        type=str,
                        help="where to save the bash script")
    parser.add_argument("--name",
                        "-n",
                        dest="corpus_name",
                        default=None,
                        help="corpus name")
    parser.add_argument("--cut_off",
                        "-c",
                        dest="cut_off",
                        type=int,
                        default=1000000,
                        help="how many lines to look at")
    parser.add_argument("--force",
                        "-f",
                        dest="force",
                        default=False,
                        action='store_true',
                        help="overwrite existing output file?")
    parser.add_argument("--system",
                        type=str,
                        default="abacist",
                        help="[abacist]|obelix")
    parser.add_argument("--lemmatisation",
                        "-l",
                        action="store_true",
                        default=False,
                        help="apply cwb-lemmatize-smor and export? [False]")
    args = parser.parse_args()

    if args.system == 'abacist':
        registry_dir = "/home/ausgerechnet/corpora/cwb/registry/"
        data_dir = "/home/ausgerechnet/corpora/cwb/data/"
    elif args.system == 'obelix':
        registry_dir = "/data/corpora/cqpweb/registry/"
        data_dir = "/data/corpora/cqpweb/corpora/"
    else:
        raise NotImplementedError()

    main(args, registry_dir, data_dir)
