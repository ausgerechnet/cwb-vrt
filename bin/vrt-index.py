#!/usr/bin/env python3

import logging
import argparse
import sys

from vrt.version import __version__
from vrt.indexing import main


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
# logging.basicConfig(format='%(message)s', level=logging.DEBUG)


def arguments():
    """Process command line arguments."""

    parser = argparse.ArgumentParser(description="cwb-vrt: Tools for processing VRT files and CWB import/export")
    parser.add_argument("-v", "--version", action="version", version="cwb-vrt %s" % __version__, help="Output version information and exit.")

    # indexing
    parser.add_argument("path_in", type=str, help="path to .vrt.gz to index")
    parser.add_argument("--path_out", "-o", dest="path_out", default=None, type=str, help="where to save the bash script")
    parser.add_argument("--force", "-f", dest="force", default=False, action='store_true', help="overwrite existing output file?")
    parser.add_argument("--name", "-n", dest="corpus_name", default=None, help="corpus name")
    parser.add_argument("--p_atts", "-p", dest="p_atts", nargs="+", type=str, default=['pos', 'lemma'], help="what p-attributes to index")
    parser.add_argument("--cut_off", "-c", dest="cut_off", type=int, default=1000000, help="how many lines to look at")
    parser.add_argument("--data_dir", type=str, default="")
    parser.add_argument("--registry_dir", type=str, default="")
    parser.add_argument("--lemmatisation", "-l", action="store_true", default=False, help="apply cwb-lemmatize-smor and export? [False]")

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()


if __name__ == "__main__":

    main(arguments())
