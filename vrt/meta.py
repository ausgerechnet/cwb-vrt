#!/usr/bin/env python3

import gzip
import os
from glob import glob
from xml.etree.ElementTree import ParseError

from pandas import DataFrame

from vrt.utils import Progress, is_gz_file
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

    return(out)


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

    def to_csv(self, p_out, compression="gzip", sep="\t"):
        """"""
        if self.df is None:
            self.get_df()
        self.df.to_csv(p_out, sep=sep, compression=compression)


def process_path(path_in, path_out, force, level, tokens, extra, idx_key):
    """"""

    # path_out
    if path_out is None:
        if path_in.endswith(".vrt.gz"):
            path_out = path_in.replace(".vrt.gz", ".tsv.gz")
        elif path_in.endswith(".xml.gz"):
            path_out = path_in.replace(".xml.gz", ".tsv.gz")
        if os.path.exists(path_out) and not force:
            raise FileExistsError("\n".join([
                f'"{path_out}" already exists',
                "you can force to overwrite by using --force / -f",
                "or by directly specifying the path using --path_out / -o"
            ]))

    # init data containers
    meta = Meta()
    extra_info = dict()
    if tokens:
        nr = 0
        nr_tokens = list()

    # iterate over file
    pb = Progress(rate=100)
    f_in = gzip.open(path_in, "rt") if is_gz_file(path_in) else open(path_in, "rt")

    for line in f_in:

        # count tokens
        if tokens:
            if line.startswith("<" + level):
                nr = 0
            elif line.startswith("</" + level):
                nr_tokens.append(nr)
            elif not line.startswith("<"):
                nr += 1

        # meta data
        if line.startswith("<"):

            for e in extra:
                if line.startswith("<" + e):
                    ex = meta2dict(line, level=e)
                    for key in ex:
                        extra_info["_".join([e, key])] = ex[key]

            if line.startswith("<" + level):
                try:
                    m = meta2dict(line, level)
                except ParseError:
                    print(f'invalid line: "{line}"')
                else:
                    for key in extra_info:
                        m[key] = extra_info[key]

            if line.startswith("</" + level):
                meta.add_meta_dict(m, idx_key=idx_key)
                pb.up()

    f_in.close()
    pb.fine()

    # add token information
    if tokens:
        meta.variables['nr_tokens'] = nr_tokens

    # save
    meta.to_csv(path_out)

    print(f"done. output writtein to {path_out}")


def main(args):
    """"""
    paths_in = glob(args.glob_in)

    for p in paths_in:

        process_path(p, args.path_out, args.force, args.level, args.tokens, args.extra, args.idx_key)