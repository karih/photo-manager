# encoding=utf-8


import os
import os.path
import logging
import argparse

from .. import app
from .. import file


def main(*args):
    # trigger a filesystem scan
    parser = argparse.ArgumentParser()
    parser.add_argument("--nofilescan",   action="store_false", default=True, dest="filescan")
    parser.add_argument("--nothumbnails", action="store_false", default=True, dest="thumbnails")
    parser.add_argument("--nophotos",     action="store_false", default=True, dest="photos")

    options = parser.parse_args(args)
    #import ipdb; ipdb.set_trace()
    if options.filescan:
        file.scan_for_missing_files()
    if options.photos:
        file.file_to_photo()
    if options.thumbnails:
        file.validate_thumbnails()
