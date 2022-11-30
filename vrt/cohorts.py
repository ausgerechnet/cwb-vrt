#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import os
from tempfile import TemporaryDirectory

from vrt.utils import MultiFileWriter, Progress, save_path_out
from vrt.vrt import dict2meta, iter_s


def process_path(path_in, path_out, force, text_old, text_new, cohort, categorical):

    f_name, path_out = save_path_out(path_in, path_out, suffix='-cohorts.vrt.gz', force=force)

    with TemporaryDirectory() as tmp_dir:

        print(f"sorting into cohorts at {tmp_dir}")
        cohorts = dict()
        paths = list()
        cohort_ids = list()
        pb = Progress()
        writer = MultiFileWriter()
        with gzip.open(path_in, "rt") as f_in:
            for text, meta in iter_s(f_in):
                cohort_meta = {c: meta[c] for c in categorical}
                cohort_id = "_".join([meta[c] for c in categorical])
                path = os.path.join(tmp_dir, cohort_id + ".vrt.gz")
                if cohort_id not in cohorts.keys():
                    cohorts[cohort_id] = cohort_meta
                    cohorts[cohort_id]['id'] = cohort_id
                    paths.append(path)
                    cohort_ids.append(cohort_id)
                writer.write(path, dict2meta(meta, level=text_new))
                writer.write(path, "\n".join(text) + "\n")
                writer.write(path, f"</{text_new}>" + "\n")
                pb.update()
        writer.close()
        pb.fine()

        print("collecting")
        pb = Progress(length=len(paths))
        with gzip.open(path_out, "wt") as f_out:
            f_out.write("<corpus>\n")
            for p, cohort_id in zip(paths, cohort_ids):
                with gzip.open(p, "rt") as f:
                    f_out.write(dict2meta(cohorts[cohort_id], level=cohort))
                    f_out.write(f.read())
                    f_out.write(f"</{cohort}>\n")
                pb.up()
            f_out.write("</corpus>")


def main(args):
    """"""

    process_path(args.path_in,
                 args.path_out,
                 args.force,
                 args.tag_old,
                 args.tag_new,
                 args.tag_cohort,
                 args.categorical)
