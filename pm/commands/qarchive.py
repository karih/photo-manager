# encoding=utf-8

import json
import sys
import os
import os.path
import logging
import argparse
import tarfile

from .. import redis
from .. import db
from .. import app
from .. import file
from .. import models

import psycopg2

logger = logging.getLogger(__name__)

def main(*args):
    #file.scan_for_new_files()
    #file.seq_file_to_photo() 
    
    print("ARGS", args)

    label = models.Label.query.filter(models.Label.label==args[0])[0]

    archive_name = os.path.join(app.config['TEMP_DIR'], '%s.tar.lzma' % args[0])
    archive = tarfile.open(archive_name, 'w:xz')

    for photo in label.photos:
        print("Adding file %s" % photo.files[0].path)
        archive.add(photo.files[0].path, arcname=os.path.basename(photo.files[0].path))
    archive.close()

    print("Wrote %s" % archive_name)

