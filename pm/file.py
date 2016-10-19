import os
import os.path
import logging
import warnings
import datetime
import hashlib


import wand

from . import app, db, helpers, models


def create_photo_thumbnails(photo):
    if not os.path.exists(photo.path_large) or not os.path.exists(photo.path_thumb):
        logging.debug("Creating thumbnails")
        thumbs = [(app.config["LARGE_SIZE"], photo.path_large), (app.config["THUMB_SIZE"], photo.path_thumb)]

        create_thumbnails(photo.path[0], thumbs)

        if app.config["SAVE_MASK"] is not None:
            os.chmod(photo.path_large, app.config["SAVE_MASK"])
            os.chmod(photo.path_thumb, app.config["SAVE_MASK"])
        if app.config["SAVE_GROUP"] is not None:
            os.chown(photo.path_large, -1, app.config["SAVE_GROUP"])
            os.chown(photo.path_thumb, -1, app.config["SAVE_GROUP"])
    else:
        pass
        #logging.debug("Thumbnails exist")

def check_if_valid_photo(file):
    try:
        helpers.extract_info(file.path)
        return True
    except ValueError as e:
        return False


def check_for_deletion(photo):
    has_files = False
    for file in photo.files:
        if os.path.exists(file.path):
            has_files = True
        else:
            logging.debug("Marking file %s deleted", file.path)
            file.deleted = True

    if not has_files:
        logging.debug("Marking photo %d deleted", photo.id)
        photo.deleted = True
    

def scan_file(file_path, force=False, make_thumbnails=True):
    logging.debug("Scanning %s", file_path.encode('utf-8', 'replace').decode('utf-8'))
    try:
        file_exists = models.File.query.filter(models.File.path == file_path).count() == 1
        hash = None
        if not file_exists or force:
            logging.info("Processing %s", file_path)
            if file_exists:
                file = models.File.query.filter(models.File.path == file_path)[0]
            else:
                file = models.File(path=file_path)

            try:
                if not file_exists or force:
                    stat = os.stat(file_path)
                    file.ctime = datetime.datetime.fromtimestamp(stat.st_ctime)
                    file.deleted = False

                with open(file_path, 'rb') as f:
                    m = hashlib.sha512()
                    m.update(f.read())
                    hash = m.hexdigest()

            except FileNotFoundError as e:
                if file_exists and not file.deleted:
                    file.deleted = True
                    warning.warn("File %s no longer exists", file_path)

            try:
                photo_exists = True
                photo = file.photo
                if photo is None and hash is not None:
                    try:
                        photo = models.Photo.query.filter(models.Photo.hash == hash).all()[0]
                    except IndexError as e:
                        photo = models.Photo(hash=hash)
                        photo_exists = False

                if photo is not None and (not photo_exists or force):
                    photo.size = os.path.getsize(file_path)
                    photo.extension = os.path.splitext(file_path)[1][1:]
                    photo.format = models.Photo.extension_to_format_key(photo.extension)

                    for key, val in helpers.extract_info(file_path).items():
                        setattr(photo, key, val)

                    db.add(photo)

                file.photo = photo

                if photo is not None and make_thumbnails:
                    create_photo_thumbnails(photo)


                
            except ValueError as e:
                logging.error("Error processing file %s (ValueError: %s)", file, e)
                file.error = str(e)
            except wand.exceptions.BlobError as e:
                logging.error("Error processing file %s (BlobError: %s)", file, e)
                file.error = str(e)
            except wand.exceptions.CorruptImageError as e:
                logging.error("Error processing file %s (CorruptImageError: %s)", file, e)
                file.error = str(e)
            except OSError as e:
                logging.error("Error processing file %s (OSError: %s)", file, e)
                file.error = str(e)
            finally:
                db.add(file)
                db.commit()
        else:
            logging.debug("Skipping %s (already in database)", file_path)
    except UnicodeEncodeError as e:
        logging.error("Error processing file %s (UnicodeEncodeError: %s)", file_path.encode('utf-8', 'replace').decode('utf-8'), e)

def scan_tree(**kwargs):
    kwargs.setdefault('force', False)
    kwargs.setdefault('make_thumbnails', True)
    for file_path in search_for_images(app.config["SEARCH_ROOT"]):
        scan_file(file_path, **kwargs)


def search_for_images(root_path):
    extensions = [extension for x in models.FORMAT_EXTENSIONS for extension in x[1]]
    logging.debug("Looking for extensions: %s", str(extensions))
    for dirname, dirnames, filenames in os.walk(root_path):
        for d in dirnames[:]:
            if (os.path.join(dirname, d) in app.config["SEARCH_EXCLUDE_ABSOLUTE_PATHS"]) or (d[0] == b".") or (d.lower() in app.config["SEARCH_EXCLUDE_DIRS"]):
                logging.debug("Skipping directory %s", os.path.join(dirname, d))
                dirnames.remove(d)

        for filename in filenames:
            if os.path.splitext(filename)[1].lower()[1:] in ('jpg', 'jpeg', 'nef', 'cr2', 'arw'):
                yield os.path.join(dirname, filename)


def create_thumbnails(filename, thumbnails):
    with wand.image.Image(filename=filename) as im:
        for size, dest in thumbnails:
            logging.debug("Creating thumbnail %s from filename %s", dest, filename)
            with im.clone() as cl:
                cl.format = 'jpeg'
                cl.auto_orient()
                cl.resize(*helpers.resize_dimensions((cl.width, cl.height), size))
                cl.save(filename=dest)


