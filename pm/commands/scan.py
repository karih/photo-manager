# encoding=utf-8

import sys
import os
import os.path
import logging
import argparse

from .. import app
from .. import file
from .. import tasks
from .. import models


def main(*args):

    if len(args) == 0:
        tasks.ScanFilesTask.queue()
        print("Started background task to scan files")

    elif args[0] == "filereadexif":
        for file in models.File.query.all():
            tasks.FileReadEXIFTask.queue(file.id)
    elif args[0] == "photocombineexif":
        for photo in models.Photo.query.all():
            tasks.PhotoCombineEXIFTask.queue(photo.id)
    elif args[0] == "photoautomerge":
        tasks.PhotoAutoMergeTask.queue()



