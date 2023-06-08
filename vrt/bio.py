def repair_bio(vrt, col=7, sep="\t", s='ner'):
    """make sure that (potentially invalid) BIOES encoding complies to
    simple BIO schema

    background: some predictors of s-attributes return BIOES encoding,
    where tags are predicted on a token-level. this BIOES is usually
    not valid, i.e. an I-{tag} might follow O, etc.

    see also Palen-Michel et al. 2021:
    - https://arxiv.org/pdf/2107.14154.pdf
    - https://github.com/bltlab/seqscore/

    we ensure valid BIO by the following rules:

    transform to BIO:
    - S-{tag} → B-{tag}
    - E-{tag} → I-{tag}

    repair BIO:
    - O → I-{tag}: O → B-{tag}
    - B-{tag1} → I-{tag2}: B-{tag1} → B-{tag2}
    - I-{tag1} → I-{tag2}: I-{tag1} → B-{tag2}

    the repaired column replaces the original column.

    additionally, BIO encoding will be transformed to s-attribute
    <{s} type={tag}> (if there is already an s-att with the same name in
    the input, the input will be ignored)

    note that we assume that any additional s-attributes stored in vrt
    break BIO encoding.

    :param iterable vrt: vrt-lines
    :param int col: column of each line that contains encoding
    :param str sep: separator for columns
    :param str s: s-attribute to store BIO encoding

    """

    lines = list()
    prev_state, prev_tag = "O", None

    for line in vrt:
        line = line.strip()     # just in case

        # ignore s-attribute lines that are named like the new s-attribute
        if line.startswith(f"<{s} ") or line.startswith(f"<{s}>") or line.startswith(f"</{s}"):
            continue

        # all other s-attributes (s, text) break BIO
        elif line.startswith("<"):
            if prev_state != "O":
                lines.append(f"</{s}>")
            lines.append(line)
            prev_state, prev_tag = "O", None

        # p-attribute lines
        else:
            line = line.split("\t")
            enc = line[col]
            if enc == "O":
                state, tag = "O", None
                if prev_state != "O":
                    lines.append(f"</{s}>")
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
                    lines.append(f"</{s}>")
                lines.append(f'<{s} type="{tag}">')
            lines.append("\t".join(line))
            prev_state, prev_tag = state, tag

    return lines
