from pandas import read_csv
from glob import glob
from vrt.vrt import iter_s, dict2meta
import gzip

path_meta = "/home/ccl/snphhein/tweepora/brexit/final-corpus-pp.tsv.gz"
paths_vrt = sorted(glob("/home/ccl/snphhein/tweepora/batches/*vrt.gz"))
path_out = "/home/ccl/snphhein/tweepora/brexit/brexit-2016-rand.vrt.gz"
meta = read_csv(path_meta, sep="\t", dtype=str)
meta['final'] = (meta['final'] == "TRUE")
meta = meta.loc[meta['final']]
meta = meta.set_index('id')


def repair_bio(vrt, col=7):

    # transform to BIO:
    # - S-{tag} → B-{tag}
    # - E-{tag} → I-{tag}

    # repair BIO:
    # - O → I-{tag}: O → B-{tag}
    # - B-{tag1} → I-{tag2}: B-{tag1} → B-{tag2}
    # - I-{tag1} → I-{tag2}: I-{tag1} → B-{tag2}

    # see also Palen-Michel et al. 2021:
    # - https://arxiv.org/pdf/2107.14154.pdf
    # - https://github.com/bltlab/seqscore/

    lines = list()
    prev_state, prev_tag = "O", None

    for line in vrt:
        line = line.strip()     # just in case

        # ignore NER lines
        if line.startswith("<ner") or line.startswith("</ner"):
            continue

        # all other s-attributes (s, text) break NER
        elif line.startswith("<"):
            if prev_state != "O":
                lines.append("</ner>")
            lines.append(line)
            prev_state, prev_tag = "O", None

        # p-attribute lines
        else:
            line = line.split("\t")
            enc = line[col]
            if enc == "O":
                state, tag = "O", None
                if prev_state != "O":
                    lines.append("</ner>")
            else:
                state, tag = enc.split("-")
                # transform to BIO
                if state == "S":
                    state = "B"
                if state == "E":
                    state = "I"
                # repair BIO
                if prev_state == "O" and state == "I":
                    state = "B"
                if (prev_state == "B" or prev_state == "I") and state == "I" and prev_tag != tag:
                    state = "B"
                line[col] = "-".join([state, tag])
            if state == "B":
                if prev_state != "O":
                    lines.append("</ner>")
                lines.append(f'<ner type="{tag}">')
            lines.append("\t".join(line))
            prev_state, prev_tag = state, tag

    return lines


# for p in paths_vrt:
with gzip.open(path_out, "wt") as f_out:
    f_out.write("<corpus>\n")
    p = paths_vrt[0]
    with gzip.open(p, "rt") as f:
        for tweet, m in iter_s(f, level="tweet"):
            idx = m['id']
            if idx in meta.index:
                m = dict(meta.loc[m['id']])
                m['id'] = idx
                tweet = repair_bio(tweet)
                f_out.write(dict2meta(m, level='tweet'))
                f_out.write("\n".join(tweet) + "\n")
                f_out.write("</tweet>\n")
    f_out.write("</corpus>\n")
