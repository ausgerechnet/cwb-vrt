#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict
import gzip
from glob import glob

from xml.etree.ElementTree import ParseError
from pandas import concat, DataFrame

from vrt.utils import Progress, is_gz_file, save_path_out
from vrt.vrt import meta2dict, remove_whitespace


def topic_checker(token_list, topic_list):
    """"""
    # TODO: include

    out = list()
    for k in topic_list:
        if k in token_list:
            out.append("1")
        else:
            out.append("0")

    return out


class Meta:
    """wrapper for creating dataframes from s-atts

    """
    def __init__(self):
        """"""
        self.variables = dict()
        self.ids = list()
        self.df = None

    def add_meta_dict(self, meta_dict, idx_key='id', path=None):
        """"""

        # just for the lolz
        meta_dict = dict(meta_dict)

        # remove TSV-breaking whitespace
        for k in meta_dict.keys():
            meta_dict[k] = remove_whitespace(meta_dict[k])

        # id
        if idx_key:
            idx = meta_dict.pop(idx_key)
            self.ids.append(idx)

        # save path-specific info
        if path is not None:
            meta_dict['path'] = path

        # add all meta data, append previously unencountered columns on the fly
        for k in meta_dict.keys():
            if k not in self.variables.keys():
                nr_missing = len(self.ids) - 1
                self.variables[k] = ["None" for i in range(nr_missing)]
            self.variables[k].append(meta_dict[k])

        # append a None for all unencountered meta data
        for k in self.variables.keys():
            if k not in meta_dict.keys():
                self.variables[k].append("None")

    def get_df(self):
        """"""
        df = DataFrame(index=self.ids, dtype=str)
        df.index.name = "id"
        for k in self.variables.keys():
            df[k] = self.variables[k]
        self.df = df
        return df

    def to_csv(self, p_out, compression="gzip", sep="\t"):
        """"""
        if self.df is None:
            self.get_df()
        self.df.to_csv(p_out, sep=sep, compression=compression)


def process_path(path_in, path_out, force, level, tokens, extra, idx_key, s_atts=[]):
    """"""

    # init data containers
    meta = Meta()
    extra_info = dict()
    if len(s_atts) > 0:
        nr_s = {s: 0 for s in s_atts}
        nr_s_regions = defaultdict(list)
    if tokens:
        nr = 0
        nr_tokens = list()

    # iterate over file
    print("collecting meta data")
    f_in = gzip.open(path_in, "rt") if is_gz_file(path_in) else open(path_in, "rt")
    pb = Progress()
    cpos = 0
    for line in f_in:
        # count tokens
        if tokens:
            if line.startswith(f"<{level}>") or line.startswith(f"<{level} "):
                nr = 0
            elif line.startswith(f"</{level}>"):
                nr_tokens.append(nr)
            elif not line.startswith("<"):
                nr += 1
                cpos += 1

        # count s-att
        for s in s_atts:
            if line.startswith(f"<{level}>") or line.startswith(f"<{level} "):
                nr_s[s] = 0
            elif line.startswith(f"</{level}>"):
                nr_s_regions[s].append(nr_s[s])
            elif line.startswith(f"</{s}>"):
                nr_s[s] += 1

        # meta data
        if line.startswith("<"):
            for e in extra:
                if line.startswith(f"<{e}>") or line.startswith(f"<{e} "):
                    ex = meta2dict(line, level=e)
                    for key in ex:
                        extra_info["_".join([e, key])] = ex[key]

            if line.startswith(f"<{level}>") or line.startswith(f"<{level} "):
                try:
                    m = meta2dict(line, level)
                except ParseError:
                    print(f'invalid line: "{line}"')
                else:
                    for key in extra_info:
                        m[key] = extra_info[key]

            if line.startswith(f"</{level}>"):
                if idx_key not in m.keys():
                    m[idx_key] = 'c_' + str(pb.c)
                meta.add_meta_dict(m, idx_key=idx_key)
                pb.up()

    f_in.close()
    pb.fine()

    # add token information
    if tokens:
        meta.variables['nr_tokens'] = nr_tokens

    for s in s_atts:
        meta.variables[f'nr_{s}'] = nr_s_regions[s]

    # save
    if path_out is not None:
        print("saving file")
        meta.to_csv(path_out)
        print(f"done. output written to {path_out}")
    else:
        return meta


def main(args):
    """"""

    paths_in = glob(args.glob_in)

    if args.path_out is not None:
        f_name, path_out = save_path_out(paths_in[0], args.path_out, suffix=".tsv.gz", force=args.force)

    ms = list()
    for p in paths_in:

        if path_out:
            p_out = None
        else:
            f_name, p_out = save_path_out(p, None, suffix=".tsv.gz", force=args.force)

        m = process_path(p,
                         p_out,
                         args.force,
                         args.level,
                         args.tokens,
                         args.extra,
                         args.index,
                         args.s_atts)

        df = m.get_df()
        if df is not None:
            ms.append(df)

    if len(ms) > 0 and path_out:
        m = concat(ms)
        m.to_csv(path_out, sep="\t", compression="gzip")
