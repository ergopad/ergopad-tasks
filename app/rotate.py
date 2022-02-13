from os import listdir
from os.path import getsize, exists
from shutil import copyfile
from argparse import ArgumentParser
import itertools


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


SIZE_5MB = 5e6
MAX_LOG_FILES_COUNT = 5


class LogRotator(object):
    def __init__(self, prefix, suffix):
        self.prefix = prefix
        self.suffix = suffix

    def __str__(self):
        return  "{}[x].{}".format(self.suffix, self.prefix)

    def __touch(self, file_name):
        open(file_name, 'w').close()

    def _gen_file_name(self, name):
        return "{}{}.{}".format(self.prefix, name, self.suffix)

    def rotate(self):
        current_log = self._gen_file_name('')
        if getsize(current_log) < SIZE_5MB:
            return

        files = [
            self._gen_file_name(i)
            for i in range(1, MAX_LOG_FILES_COUNT + 1)
        ]

        for file in files:
            if not exests(file):
                self.__touch(f)

        for older, newer in pairwise(reversed([current_log] + files)):
            copyfile(newer, older)

        self.__touch(current_log)


if __name__ == '__main__':
    parser = ArgumentParser(description="Rotate log files")
    parser.add_argument("-prefix", help="log file prefix")
    parser.add_argument("-suffix", help="log file suffix")

    args = parser.parse_args()

    log_rotator = LogRotator(args.prefix, args.suffix)
    log_rotator.rotate()
