import argparse
import gzip
import os
from glob import glob
from xml.etree.ElementTree import ParseError

from cutils.times import Progress
from cutils.vrt import Meta, meta2dict


def main(path_in, path_out, level, extra=[], tokens=False):

    meta = Meta()
    pb = Progress(rate=100)
    nr = 0
    nr_tokens = list()

    if path_in.endswith(".gz"):
        f_in = gzip.open(path_in, "rt")

    else:
        f_in = open(path_in, "rt")

    extra_info = dict()

    for line in f_in:
        if tokens:
            if line.startswith("<" + level):
                nr = 0
            elif line.startswith("</" + level):
                nr_tokens.append(nr)
            elif not line.startswith("<"):
                nr += 1

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
                    print("invalid line:")
                    print(line)
                else:
                    for key in extra_info:
                        m[key] = extra_info[key]

            if line.startswith("</" + level):
                meta.add_meta_dict(m)
                pb.up()

    f_in.close()

    pb.fine()

    if tokens:
        meta.variables['nr_tokens'] = nr_tokens

    meta.to_csv(path_out)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("glob_in",
                        help="path(s) to .[xml|vrt].gz",
                        type=str)
    parser.add_argument("-o",
                        "--path_out",
                        help="path to .tsv.gz",
                        default=None,
                        type=str)
    parser.add_argument("-s",
                        "--s_att",
                        dest='s_att',
                        help="s-att that contains meta data [text]",
                        default="text",
                        type=str)
    parser.add_argument("-t",
                        "--tokens",
                        dest='tokens',
                        help="count tokens? [False]",
                        action='store_true',
                        default=False)
    parser.add_argument("-e",
                        "--extra",
                        dest='extra',
                        help="s-attributes with extra info (above level)",
                        type=str,
                        nargs='+',
                        default=[])
    args = parser.parse_args()

    paths_in = glob(args.glob_in)

    for p in paths_in:

        if args.path_out is None:

            if p.endswith(".vrt.gz"):
                path_out = p.replace(".vrt.gz", ".tsv.gz")
            elif p.endswith(".xml.gz"):
                path_out = p.replace(".xml.gz", ".tsv.gz")

            if os.path.exists(path_out):
                raise FileExistsError((
                    '"%s" already exists!\n'
                    "you can force to overwrite by directly "
                    "specifying the path using --path_out or -o"
                ) % path_out)
        else:
            path_out = args.path_out

        main(p, path_out, args.s_att, args.extra, args.tokens)
