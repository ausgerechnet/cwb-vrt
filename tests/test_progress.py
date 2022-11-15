from time import sleep

from vrt.utils import Progress


def test_progress():
    print()
    pb = Progress(rate=1)
    for _ in range(100):
        sleep(.1)
        pb.up()
    pb.fine()


def test_progress_length():
    print()
    pb = Progress(rate=1, length=100)
    for _ in range(100):
        sleep(.1)
        pb.up()
