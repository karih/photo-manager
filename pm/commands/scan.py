# encoding=utf-8

import sys
import os
import os.path
import logging
import argparse

from .. import app
from .. import file


def main(*args):
    # Elements to this function:
    # - scan for photos
    # - scan library and delete photos that no longer physically exist
    # - scan for exif information
    # - make sure thumbnails exist for all photos
    # - refresh cache

    parser = argparse.ArgumentParser()
    #parser.add_argument("--nonewfilescan",    action="store_false", default=True, dest="filescan")
    #parser.add_argument("--novalidatefiles",  action="store_false", default=True, dest="validatefiles")
    #parser.add_argument("--novalidatephotos", action="store_false", default=True, dest="validatephotos")
    #parser.add_argument("--nothumbnails",     action="store_false", default=True, dest="thumbnails")
    #parser.add_argument("--nophotos",         action="store_false", default=True, dest="photos")
    #options = parser.parse_args(args)

    scan_new_files = True
    run_through_exif = False

    if scan_new_files:
        ### Scan for new files
        # Search for files not already in the `files` table and proceed
        # to add them
        file.scan_for_new_files()
        # Search through the files table for orphans (no photo_id), extract
        # exif information of those photos and either create a new photo
        # object or attach to an existing one
        file.seq_file_to_photo() 
        # Next up, creating thumbnails 
        file.seq_create_thumbnails()

        # Finally, build directory cache
    if run_through_exif:
        ### Update photo object exif information
        file.seq_update_exif()
        pass

    sys.exit(0)


    if options.filescan:
        logging.info("Scanning for new files")

    if options.photos:
        file.file_to_photo()
    if options.thumbnails:
        file.validate_thumbnails()
