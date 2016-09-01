# encoding=utf-8


import os
import os.path
import logging

import wand

from ..models import ImageFile, db_session
from .. import app


def find_all_files(root_path):
    for dirname, dirnames, filenames in os.walk(root_path):
        for d in dirnames[:]:
            if (os.path.join(dirname, d) in app.config["SEARCH_EXCLUDE_ABSOLUTE_PATHS"]) or (d[0] == b".") or (d.lower() in app.config["SEARCH_EXCLUDE_DIRS"]):
                logging.info("Skipping directory %s", os.path.join(dirname, d))
                dirnames.remove(d)

        for filename in filenames:
            if os.path.splitext(filename)[1].lower()[1:] in ('jpg', 'jpeg', 'nef', 'cr2', 'arw'):
                yield os.path.join(dirname, filename)


def find_and_add_files():
    for file in find_all_files(app.config["SEARCH_ROOT"]):
        processed = 0
        skipped = 0
        failed = 0

        try:
            if ImageFile.query.filter(ImageFile.path == file).count() < 1:
                logging.info("Processing %s", file)
                try:
                    image = ImageFile.load(file)
                    db_session.add(image)
                    db_session.commit()
                except wand.exceptions.BlobError as e:
                    logging.error("Error processing file %s (BlobError: %s)", file, e)
                except wand.exceptions.CorruptImageError as e:
                    logging.error("Error processing file %s (CorruptImageError: %s)", file, e)
                except OSError as e:
                    logging.error("Error processing file %s (OSError: %s)", file, e)
            else:
                logging.debug("Skipping %s (already in database)", file)
        except UnicodeEncodeError as e:
            logging.error("Error processing file %s (UnicodeEncodeError: %s)", file.encode('utf-8', 'replace').decode('utf-8'), e)

def main(*args):
    find_and_add_files()
