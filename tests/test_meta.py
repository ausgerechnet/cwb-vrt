from vrt.meta import process_path


def test_process_path():

    process_path(
        "tests/data/tagesschau-mini.vrt.gz",
        None,
        True,
        "article",
        True,
        [],
        None
    )
