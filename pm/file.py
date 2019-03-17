import re
import os
import os.path
import logging
import datetime
import hashlib

from . import app, db, helpers, models, image_processing, exif


logger = logging.getLogger(__name__)


def seq_create_thumbnails():
    """ Ensure every photo object has a corresponding thumbnail """

    def pre(offset, limit, rows):
        logging.debug("validate_thumbnails: starting batch %d-%d/%d" % (offset, offset+limit, rows))

    for photo in models.model_iterator(models.Photo.query, pre, lambda **kwargs: db.commit()):
        image_processing.create_photo_thumbnails(photo)

###############################
""" not gone through review """

def seq_update_exif():
    def pre(offset, limit, rows):
        logging.debug("file_to_photo: starting batch %d-%d/%d" % (offset, offset+limit, rows))

    for photo in models.model_iterator(
            models.Photo.all(),
            pre, 
            lambda **kwargs: db.commit()
        ):
        update_exif(photo)

def update_exif(photo_obj, commit=False):
    raise Exception("Funky implementation")
    metadata = photo_obj 

    for key, val in metadata.get_dict().items():
        setattr(photo_obj, key, val)

    if commit:
        db.commit()

def check_for_deletion(file):
    def file_is_filtered(path):
        for sf in app.config["SEARCH_EXCLUDE_FILES"]:
            if re.fullmatch(sf, path) is not None:
                return True

        while True:
            path, _ = os.path.split(path)
            if path == "/":
                break
            for sd in app.config["SEARCH_EXCLUDE_DIRS"]:
                if re.fullmatch(sd, path) is not None:
                    return True
        return False

    changed = False
    if file.deleted:
        if not file_is_filtered(file.path) and os.path.exists(file.path):
            logging.warning("File %d:%s marked deleted but exists", file.id, file.path)
    else:
        if file_is_filtered(file.path):
            logging.debug("Marking file %d:%s deleted since path is filtered", file.id, file.path)
            file.deleted = True
            changed = True
        elif not os.path.exists(file.path):
            logging.debug("Marking file %d:%s deleted since file no longer exists", file.id, file.path)
            file.deleted = True
            changed = True

    return changed


def scan_for_deleted_files():
    """ Scan the file registry for deleted files """

    def pre(offset, limit, rows):
        logging.debug("file_to_photo: starting batch %d-%d/%d" % (offset, offset+limit, rows))

    for file in models.model_iterator(models.File.query.filter(models.File.error == None).filter(models.File.deleted == False), pre, lambda **kwargs: db.commit()):
        if check_for_deletion(file):
            db.add(file)

