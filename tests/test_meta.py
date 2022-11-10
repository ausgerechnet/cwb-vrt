from vrt.meta import process_path


def test_main():

    process_path(
        "tests/data/tagesschau-mini.vrt.gz",
        None,
        True,
        "article",
        True,
        [],
        None
    )
