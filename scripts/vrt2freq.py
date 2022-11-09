import argparse
import gzip

from cutils.cwb.vrt import meta2dict
from cutils.times import Progress

# get script arguments
parser = argparse.ArgumentParser()

parser.add_argument("--path_in",
                    help="path to gzipped XML file",
                    type=str)

parser.add_argument("--path_out",
                    help="path to file to save tsv to",
                    type=str)

parser.add_argument("--path_lemmas",
                    help="path to lemmas (one lemma per line)",
                    type=str)

args = parser.parse_args()
path_in = args.path_in
path_out = args.path_out
path_lemmas = args.path_lemmas


topics = set()
with open(path_lemmas, "rt") as f:
    for line in f:
        topics.add(line.rstrip())
topics = list(topics)

# also use the hashtagified topics
topics += ["#" + t for t in topics]


def lemmas_checker(lemma_list, topic_list):
    # convert both lists to lower
    lemma_list = [l.lower() for l in lemma_list]
    topic_list = sorted([t.lower() for t in topic_list])
    out = list()
    for k in topic_list:
        if k in lemma_list:
            out.append("1")
        else:
            out.append("0")
    return(out)


if __name__ == '__main__':
    pb = Progress()
    with gzip.open(path_in, "rt") as f_vrt, gzip.open(path_out, "wt") as f_df:
        f_df.write(",".join(["idx", "date", "rt", "dedup"]))
        f_df.write(",")
        f_df.write(",".join(sorted(topics)))
        f_df.write("\n")

        for line in f_vrt:
            if line.startswith("<text"):
                meta_text = meta2dict(line)
                rt_status = meta_text['rt']
                duplicate_status = meta_text['duplicate']
            if line.startswith("<tweet"):
                meta = meta2dict(line, level="tweet")
                idx = meta['id']
                date = meta['date']
                lemmas = list()
                pb.up()
            elif line.startswith("</tweet>"):
                f_df.write(",".join([idx, date, rt_status, duplicate_status]))
                f_df.write(",")
                topics_info = lemmas_checker(lemmas, topics)
                f_df.write(",".join(topics_info))
                f_df.write("\n")
            elif not line.startswith("<"):
                row = line.rstrip().split("\t")
                if len(row) == 3:
                    lemmas.append(row[2])

    pb.fine()
