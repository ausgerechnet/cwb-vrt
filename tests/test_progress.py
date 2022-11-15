from time import sleep

from vrt.utils import Progress


def test_progress():
    print()
    pb = Progress(rate=1)
    for _ in range(100):
        sleep(.02)
        pb.up()
    pb.fine()


def test_progress_length():
    print()
    pb = Progress(rate=1, length=100000)
    for _ in range(100000):
        sleep(.0001)
        pb.up()
