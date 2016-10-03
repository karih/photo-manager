# encoding=utf-8


import os
import os.path
import logging

import wand

from .. import app
from .. import file


def main(*args):
    # trigger a filesystem scan
    file.scan_tree()
