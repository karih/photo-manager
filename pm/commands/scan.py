# encoding=utf-8


import os
import os.path

import wand

from ..models import ImageFile, db_session
from .. import app


def find_all_files(root_path):
    for dirname, dirnames, filenames in os.walk(root_path):
        for d in dirnames[:]:
            if (d[0] == ".") or (d.lower() in ('tmp', 'temp', 'backup')):
                dirnames.remove(d)

        for filename in filenames:
            if os.path.splitext(filename)[1].lower()[1:] in ('jpg', 'jpeg', 'nef', 'cr2', 'arw'):
                yield os.path.join(dirname, filename)


def find_and_add_files():
    for file in find_all_files(app.config["SEARCH_ROOT"]):
        processed = 0
        skipped = 0
        failed = 0

        if ImageFile.query.filter(ImageFile.path == file).count() < 1:
            try:
                image = ImageFile.load(file)
                db_session.add(image)
                db_session.commit()
            except wand.exceptions.BlobError as e:
                print("Error processing file %s (BlobError: %s)" % (file, e))
            except OSError as e:
                print("Error processing file %s (OSError: %s)" % (file, e))

def main(*args):
    find_and_add_files()
