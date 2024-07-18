from vrt.deduplicate import fingerprint
from pprint import pprint


def test_process_path():

    pprint(fingerprint(
        "tests/data/tweet-duplicates.vrt.gz",
        level="tweet"
    ))
