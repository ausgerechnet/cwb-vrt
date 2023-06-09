#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hashlib import md5
from pandas import DataFrame, NamedAgg
from glob import glob
import gzip

from vrt.utils import save_path_out


def fingerprint(path_in, level="s", col=0, sep="\t"):
    """
    extract fingerprints for each region based on p-atts stored in {col}
    """
    regions = list()
    with gzip.open(path_in, "rt") as f:

        region = list()         # lines of current region
        nr = 0
        for line in f:
            line = line.strip()

            if line.startswith("<{level}>") or line.startswith("<{level} "):
                # TODO: parse meta-data?
                pass

            if line.startswith(f"</{level}>"):
                regions.append({
                    "path": path_in,
                    "region_nr": nr,
                    # "region": " ".join(region),
                    "region_length": len(region),
                    "region_hash": md5(" ".join(region).encode()).hexdigest()
                })
                region = list()
                nr += 1

            # p-attribute lines
            elif not line.startswith("<"):
                p_att = line.split(sep)[col]
                region.append(p_att)

    return regions


def detect(records, order=['path', 'region_nr'], keep='last'):
    """
    detect duplicates in records
    return a dataframe containing
    - {id_col}
    - nr_regions
    - nr_tokens
    - cluster_id
    - dup
    """

    # create dataframe and sort according to id_cols
    ndup = DataFrame.from_records(records).sort_values(by=order)

    # detect duplicates
    ndup['duplicate'] = ndup.duplicated(subset=['region_hash'], keep=keep)

    # identify clusters
    ndup['id'] = ndup[order].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
    clusters = ndup.groupby('region_hash').agg(
        nr_regions=NamedAgg(column='region_length', aggfunc='count'),
        nr_tokens=NamedAgg(column='region_length', aggfunc='sum'),
        cluster_id=NamedAgg(column='id', aggfunc=keep)
    ).reset_index()

    ndup = ndup.merge(clusters, on='region_hash').sort_values(by=order).set_index(order).drop('region_hash', axis=1)

    return ndup


def main(args):

    paths_in = glob(args.glob_in)
    f_name, path_out = save_path_out(paths_in[0], args.path_out, suffix='.dup.gz', force=args.force)

    print("collecting fingerprints")
    region_records = list()
    for p in paths_in:
        print(".. " + p)
        region_records.extend(fingerprint(p, args.level))

    if len(region_records) == 0:
        print(f"can't find any '{args.level}' regions, aborting")

    else:
        print("detecting duplicates")
        ndup = detect(region_records, keep=args.keep)
        print(".. stats:")
        print(ndup['duplicate'].value_counts())
        ndup.to_csv(path_out, sep="\t", compression="gzip")
