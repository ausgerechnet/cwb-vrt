#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gzip
from glob import glob
from pandas import concat, read_csv, NamedAgg

from vrt.utils import Progress
from vrt.vrt import dict2meta


def read_cohorts_info(paths_info, sep="\t"):
    """
    obligatory column in each dataframe: cohort_idx
    """

    print("gathering cohorts information")
    pb = Progress(length=len(paths_info), rate=1)
    dfs = list()
    for p in paths_info:
        dfs.append(read_csv(p, sep=sep, dtype=str))
        pb.up()

    print("concatenating")
    df = concat(dfs)
    df = df.fillna("")

    print("deduplicating")
    columns = list(df.columns.copy())
    if 'counts' in df.columns:
        columns.remove('counts')
        df['counts'] = df['counts'].astype(int)
        df = df.groupby(columns).agg(
            counts=NamedAgg(column='counts', aggfunc=sum)
        )
        df = df.reset_index()
    else:
        df = df.drop_duplicates()

    return df.set_index("cohort_idx")


def write_cohorts(paths_in, path_out, corpus_name, meta, level='text'):
    """
    obligatory column in meta: path, id
    """

    # loop through files and write
    print("writing cohorts")
    with gzip.open(path_out, "wt") as f_out:

        f_out.write(f'<corpus name="{corpus_name}">\n')

        pb = Progress(length=len(meta), rate=1)
        for row in meta.iterrows():
            m = dict(row[1])
            path = m.pop('path')

            f_out.write(dict2meta(m, level=level))
            with gzip.open(path, "rt") as f:
                for line in f:
                    f_out.write(line)
            f_out.write(f"</{level}>\n")

            pb.up()

        f_out.write("</corpus>\n")


def main(args):
    """"""

    corpus_name = args.path_out.split("/")[-1].split(".vrt.gz")[0].upper() if args.name is None else args.name
    paths_in = glob(args.glob_in)

    if args.cohorts_info:
        # read cohorts info
        meta = read_cohorts_info(glob(args.cohorts_info))
        meta = meta.sort_values(by=args.order)
        meta = meta.rename({'cohort_clear': 'id'}, axis=1)
        # add paths
        meta['path'] = None
        for p in paths_in:
            cohort_idx = p.split("/")[-1].split(".vrt.gz")[0]
            meta.loc[cohort_idx, 'path'] = p
    else:
        meta = None

    write_cohorts(paths_in, args.path_out, corpus_name, meta)
