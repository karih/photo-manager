import re
import os
import os.path
import logging
import datetime
import hashlib

from . import app, db, helpers, models, image_processing, exif


def check_if_valid_photo(file):
    try:
        helpers.extract_info(file.path)
        return True
    except ValueError as e:
        return False


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


def search_for_images(root_path):
    """ 
        A generator that takes a root path `root_path` and spits out all files
        below which have common image file extensions (`FORMAT_EXTENSIONS`) and 
        not excluded through `SEARCH_EXCLUDE_DIRS` or `SEARCH_EXCLUDE_FILES`.
    """

    extensions = [extension for x in models.FORMAT_EXTENSIONS for extension in x[1]]
    logging.debug("Looking for extensions: %s", str(extensions))
    for dirname, dirnames, filenames in os.walk(root_path):
        for d in dirnames[:]:
            for sd in app.config["SEARCH_EXCLUDE_DIRS"]:
                if re.fullmatch(sd, os.path.join(dirname, d)) is not None:
                    logging.debug("Skipping directory %s", os.path.join(dirname, d))
                    dirnames.remove(d)
                    break

        for filename in filenames:
            for sf in app.config["SEARCH_EXCLUDE_FILES"]:
                if re.fullmatch(sf, os.path.join(dirname, filename)) is not None:
                    logging.debug("Skipping file %s", os.path.join(dirname, filename))
                    break
            else:
                if os.path.splitext(filename)[1].lower()[1:] in extensions:
                    yield os.path.join(dirname, filename)


def scan_for_missing_files(**kwargs):
    """ Scan the filesystem for images not present in the database """
    for file_path in search_for_images(app.config["SEARCH_ROOT"]):
        logging.debug("Scanning %s", file_path.encode('utf-8', 'replace').decode('utf-8'))

        try:
            file = models.File.query.filter(models.File.path == file_path)[0]
            continue
        except IndexError:
            with open(file_path, 'rb') as f:
                m = hashlib.sha512()
                m.update(f.read())
                hash = m.hexdigest()

            stat = os.stat(file_path)
            file = models.File(
                path=file_path,
                format=models.File.extension_to_format_key(os.path.splitext(file_path)[1][1:]),
                ctime=datetime.datetime.fromtimestamp(stat.st_ctime),
                size=stat.st_size,
                hash=hash
            )

            db.add(file)
    db.commit()


def scan_for_deleted_files():
    """ Scan the file registry for deleted files """

    def pre(offset, limit, rows):
        logging.debug("file_to_photo: starting batch %d-%d/%d" % (offset, offset+limit, rows))

    for file in models.model_iterator(models.File.query.filter(models.File.error == None).filter(models.File.deleted == False), pre, lambda **kwargs: db.commit()):
        if check_for_deletion(file):
            db.add(file)


def file_to_photo():
    """ 
        Create photo object from files, extract exif info.
        We will re-use a photo object if the existing files have the same
        exif datetime *and* filename (ignoring extension).
    """

    drop_dir_ext = lambda x: os.path.splitext(os.path.basename(x))[0]
    def pre(offset, limit, rows):
        logging.debug("file_to_photo: starting batch %d-%d/%d" % (offset, offset+limit, rows))

    for file in models.model_iterator(models.File.query.filter(models.File.photo_id == None).filter(models.File.error == None).filter(models.File.deleted == False), pre, lambda **kwargs: db.commit()):
        metadata = exif.exiftool_extract_info(file.path)
        try:
            photo = [f for f in models.File.query.filter(models.File.photo_id != None).filter(models.File.path.contains(drop_dir_ext(file.path))) if drop_dir_ext(f.path) == drop_dir_ext(file.path) and f.photo.date == metadata["date"]][0].photo
            file.photo = photo
        except IndexError:
            photo = models.Photo(**metadata)
            file.photo = photo
            db.add(photo)


def validate_thumbnails():
    """ Ensure every photo object has a corresponding thumbnail """

    def pre(offset, limit, rows):
        logging.debug("validate_thumbnails: starting batch %d-%d/%d" % (offset, offset+limit, rows))

    for photo in models.model_iterator(models.Photo.query, pre):
        image_processing.create_photo_thumbnails(photo)


def group_photos():
    """ Group photos into objects """
    pass
