#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import os
import xml
from collections import defaultdict

from vrt.utils import Progress, is_gz_file, save_path_out
from vrt.vrt import meta2dict


def create_file(path_in, corpus_name, registry_dir, data_dir, p_atts, s_atts, lemmatisation=False, charset="utf8"):
    """
    create shell script for executing cwb-encode
    with default options:
    global: -xsBC -9
    s-attributes: -S {s}:0 or -S {s}:0+..., <corpus> will be ignored
    """

    lines = [
        '#!/bin/bash',
        '',
        f'path_in="{path_in}"',
        '',
        f'corpus_name="{corpus_name}"',
        '',
        f'registry_dir="{registry_dir}"',
        f'data_dir="{data_dir}"',
        '',
        'registry_file="$registry_dir${corpus_name,,}"',
        'data_subdir="$data_dir${corpus_name,,}"',
        '',
        'echo "data directory: $data_subdir"',
        'mkdir -p $data_subdir',
        '',
        'echo "cwb-encode (registry file: $registry_file)"',
        f'cwb-encode -d $data_subdir -f $path_in -R "$registry_file" -xsBC -c {charset} -9 {p_atts} {s_atts}',
        '',
        'echo "cwb-make"',
        'cwb-make -r $registry_dir -M 4096 -V "$corpus_name"',
        ''
    ]

    if lemmatisation:

        path_out = path_in.replace(".vrt.gz", "-lemma.vrt")

        # explicitly export p-att 'word' and 'lemma' alongside all other p-atts
        p_atts = " ".join(["-P word", p_atts, "-P lemma"])

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


def guess_attributes(path_in, cut_off, ignore_corpus=False):
    """"""

    print(f"guessing attributes from first {cut_off} lines...")

    s_atts = defaultdict(set)
    nr_p_atts = 1
    nr_p_lines = 0
    nr_s_lines = 0

    f = gzip.open(path_in, "rt") if is_gz_file(path_in) else open(path_in, "rt")
    pb = Progress(length=cut_off) if cut_off > 0 else Progress()
    for line in f:

        if line.startswith("<?") or line.startswith("<!"):
            # xml declaration or comment
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

    if cut_off <= 0 or pb.c < pb.length:
        pb.fine()

    f.close()

    # post-process s-attributes
    s_atts_new = list()
    for s in s_atts.keys():

        if ignore_corpus and s == 'corpus':       # ignore <corpus>
            continue

        if len(s_atts[s]) == 0:  # no annotation
            new = s + ":0"
            s_atts_new.append(new)
        else:                    # annotation
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

    row = line.strip().rstrip(">").lstrip("<")
    typ = row.split(" ")[0]

    try:
        ann = set(meta2dict(line, level=typ).keys())
    except xml.etree.ElementTree.ParseError:
        print("error when parsing s-attribute:")
        print(line)
    return typ, ann


def process_path(path_in, path_out, force, name, p_atts, cut_off, data_dir, registry_dir, lemmatisation):
    """"""

    # path_in
    f_name, path_out = save_path_out(path_in, path_out, suffix='.sh', force=force)

    # corpus_name
    corpus_name = f_name.upper() if name is None else name.upper()

    # attributes
    atts = guess_attributes(path_in, cut_off)

    # post-process positional attributes
    if atts['nr_p_atts'] > len(p_atts) + 1:
        print(f"warning: saw more p-attributes ({atts['nr_p_atts'] - 1}) than provided p-attribute names (excluding primary layer)")
        padding = atts['nr_p_atts'] - (len(p_atts) + 1)
        p_atts = p_atts + [f"p_att_{c}" for c in range(padding)]

    # convert attributes to strings
    p_atts = "-P " + " -P ".join(p_atts[: atts['nr_p_atts'] - 1]) if atts['nr_p_atts'] > 1 else ""
    print(f"p-attributes: {p_atts}")
    s_atts = "-S " + " -S ".join(atts['s_atts'])
    print(f"s-attributes: {s_atts}")

    # create file contents
    file_contents = create_file(path_in, corpus_name, registry_dir, data_dir, p_atts, s_atts, lemmatisation)

    # write
    with open(path_out, "wt") as f:
        f.write(file_contents)

    # make the script executable
    os.system(f"chmod u+x {path_out}")

    # status
    print(f"output written to {path_out}")


def main(args):
    """"""

    process_path(args.path_in,
                 args.path_out,
                 args.force,
                 args.name,
                 args.p_atts,
                 args.cut_off,
                 args.data_dir,
                 args.registry_dir,
                 args.lemmatisation)
