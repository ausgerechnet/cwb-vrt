#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from glob import glob
from hashlib import md5
from pandas import DataFrame, NamedAgg
from unicodedata import category
import gzip
import re

from vrt.utils import save_path_out
from vrt.vrt import meta2dict


def replace_urls(text, by='URL'):

    url = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    text = url.sub(by, text)

    return text


def replace_mentions(text, by='@USER'):

    mention = re.compile(r'@\w+')
    text = mention.sub(by, text)

    return text


def replace_rts(text, by=''):

    rt = re.compile(r'^RT$')
    text = rt.sub(by, text)

    return text


def text_normalise(text):
    """remove all
    - URLs
    - RT markers ("RT")
    - mentions ("@USER")
    - non-letters
    and convert to lower
    """
    text = replace_urls(text, "")
    text = replace_mentions(text, "")
    text = replace_rts(text, "")
    text = ''.join([c for c in text if category(c).startswith('L')])
    return text.lower()


def fingerprint(path_in, level="s", col=0, sep="\t", normalise=True):
    """
    extract fingerprints for each region based on p-atts stored in {col}
    """
    regions = list()
    with gzip.open(path_in, "rt") as f:

        region = list()         # lines of current region
        nr = 0
        meta = dict()

        for line in f:
            line = line.strip()
            if line.startswith(f"<{level}>") or line.startswith(f"<{level} "):
                meta = meta2dict(line, level=level)
                meta['path'] = path_in

            if line.startswith(f"</{level}>"):
                region_fingerprint = {
                    'region_nr': nr,
                    'region_length': len(region),
                    'region_hash': md5(''.join(region).encode()).hexdigest()
                }
                regions.append({**meta, **region_fingerprint})
                region = list()
                nr += 1

            # p-attribute lines
            elif not line.startswith("<"):
                p_att = line.split(sep)[col]
                if normalise:
                    p_att = text_normalise(p_att)
                region.append(p_att)

    return regions


def detect(records, order=['path', 'region_nr'], keep='last', normalise=True):
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
    ndup['internal_id'] = ndup[order].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
    clusters = ndup.groupby('region_hash').agg(
        nr_regions=NamedAgg(column='region_length', aggfunc='count'),
        nr_tokens=NamedAgg(column='region_length', aggfunc='sum'),
        cluster_id=NamedAgg(column='internal_id', aggfunc=keep)
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
        region_records.extend(fingerprint(p, args.level, col=0, sep="\t", normalise=args.normalise))

    if len(region_records) == 0:
        print(f"can't find any '{args.level}' regions, aborting")

    else:
        print("detecting duplicates")
        ndup = detect(region_records, keep=args.keep)
        print(".. stats:")
        print(ndup['duplicate'].value_counts())
        ndup.to_csv(path_out, sep="\t", compression="gzip")
