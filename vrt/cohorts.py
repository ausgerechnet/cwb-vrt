#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import os
from collections import defaultdict
from tempfile import TemporaryDirectory

from vrt.utils import MultiFileWriter, Progress, save_path_out
from vrt.vrt import dict2meta, iter_s


def process_path(path_in, path_out, force, tag_old, tag_new, cohort, categorical, memory=False):

    f_name, path_out = save_path_out(path_in, path_out, suffix='-cohorts.vrt.gz', force=force)

    if memory:

        print("sorting into cohorts in memory")
        cohorts = defaultdict(list)
        cohorts_id = list()
        cohorts_meta = dict()
        pb = Progress()
        with gzip.open(path_in, "rt") as f_in:
            for text, meta in iter_s(f_in, level=tag_old):
                cohort_id = "_".join([meta[c] for c in categorical])
                cohort_meta = {c: meta[c] for c in categorical}
                path = os.path.join(cohort_id + ".vrt.gz")
                if cohort_id not in cohorts_meta.keys():
                    cohorts_meta[cohort_id] = cohort_meta
                    cohorts_meta[cohort_id]['id'] = cohort_id
                    cohorts_id.append(cohort_id)
                cohorts[cohort_id].append(dict2meta(meta, level=tag_new))
                cohorts[cohort_id].append("\n".join(text) + "\n")
                cohorts[cohort_id].append(f"</{tag_new}>" + "\n")
                pb.up()
        pb.fine()

        print("writing")
        pb = Progress(length=len(cohorts))
        with gzip.open(path_out, "wt") as f_out:
            f_out.write("<corpus>\n")
            for cohort_id in cohorts_id:
                f_out.write(dict2meta(cohorts_meta[cohort_id], level=cohort))
                f_out.write("".join(cohorts[cohort_id]))
                f_out.write(f"</{cohort}>\n")
                pb.up()
            f_out.write("</corpus>")

    else:
        with TemporaryDirectory() as tmp_dir:

            print(f"sorting into cohorts at {tmp_dir}/")
            cohorts_id = list()
            cohorts_meta = dict()
            paths = list()
            pb = Progress()
            writer = MultiFileWriter()
            with gzip.open(path_in, "rt") as f_in:
                for text, meta in iter_s(f_in, level=tag_old):
                    cohort_id = "_".join([meta[c] for c in categorical])
                    cohort_meta = {c: meta[c] for c in categorical}
                    path = os.path.join(tmp_dir, cohort_id + ".vrt.gz")
                    if cohort_id not in cohorts_meta.keys():
                        cohorts_meta[cohort_id] = cohort_meta
                        cohorts_meta[cohort_id]['id'] = cohort_id
                        cohorts_id.append(cohort_id)
                        paths.append(path)
                    writer.write(path, dict2meta(meta, level=tag_new))
                    writer.write(path, "\n".join(text) + "\n")
                    writer.write(path, f"</{tag_new}>" + "\n")
                    pb.up()
            writer.close()
            pb.fine()

            print("collecting")
            pb = Progress(length=len(paths))
            with gzip.open(path_out, "wt") as f_out:
                f_out.write("<corpus>\n")
                for p, cohort_id in zip(paths, cohorts_id):
                    with gzip.open(p, "rt") as f:
                        f_out.write(dict2meta(cohorts_meta[cohort_id], level=cohort))
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
                 args.categorical,
                 args.memory)
