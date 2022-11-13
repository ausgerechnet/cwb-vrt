from vrt.indexing import process_path


def test_process_path():

    process_path(
        "tests/data/tagesschau-mini.vrt.gz",
        None,
        True,
        None,
        ['pos', 'lemma'],
        1000000,
        "/usr/local/share/cwb/data/",
        "/usr/local/share/cwb/registry/",
        True
    )
