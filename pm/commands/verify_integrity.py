# encoding = utf-8

import re
import sys
import logging
import os
import os.path

from .. import models
from .. import file
from .. import db

from . import helpers

def main(*args):
    """ Drops and rebuilds the elasticsearch index """

    for photo in helpers.get_photo_batch_iterator():
        file.check_for_deletion(photo)

        valid = list(map(file.check_if_valid_photo, [f for f in photo.files if not f.deleted]))
        if not photo.deleted and sum(valid) == 0:
            logging.info("Marking photo %d for deletion due to zero parsable files", photo.id)
            photo.deleted = True
        elif sum(valid) != len(valid):
            logging.warning("Photo %d has a mixture of valid and invalid files", photo.id)

        if photo.deleted:
            if os.path.exists(photo.path_large):
                os.unlink(photo.path_large)
            if os.path.exists(photo.path_thumb):
                os.unlink(photo.path_thumb)
            continue

        file.create_photo_thumbnails(photo)


