import re
import os
import os.path
import logging
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


    has_files = False
    for file in photo.files:
        if file.deleted:
            if not file_is_filtered(file.path) and os.path.exists(file.path):
                logging.warning("File %d:%s marked deleted but exists", file.id, file.path)
        else:
            if file_is_filtered(file.path):
                logging.debug("Marking file %d:%s deleted since path is filtered", file.id, file.path)
                file.deleted = True
            elif not os.path.exists(file.path):
                logging.debug("Marking file %d:%s deleted since file no longer exists", file.id, file.path)
                file.deleted = True
            else:
                has_files = True

    if not photo.deleted and not has_files:
        logging.debug("Marking photo %d deleted", photo.id)
        photo.deleted = True
    

def scan_file(file_path, force=False, make_thumbnails=True):
    logging.debug("Scanning %s", file_path.encode('utf-8', 'replace').decode('utf-8'))
    try:
        try:
            file = models.File.query.filter(models.File.path == file_path)[0]
        except IndexError:
            file = None
        hash = None
        if force or file is None or file.deleted:
            logging.info("Processing %s", file_path)

            if file is None:
                file = models.File(path=file_path)

            try:
                if force or file.id is None:
                    stat = os.stat(file_path)
                    file.ctime = datetime.datetime.fromtimestamp(stat.st_ctime)

                file.deleted = False

                with open(file_path, 'rb') as f:
                    m = hashlib.sha512()
                    m.update(f.read())
                    hash = m.hexdigest()

            except FileNotFoundError as e:
                logging.warning("File %s disappeared", file_path)
                return

            try:
                photo = file.photo
                if photo is None:
                    try:
                        photo = models.Photo.query.filter(models.Photo.hash == hash).all()[0]
                    except IndexError:
                        photo = models.Photo(hash=hash)

                if force or photo.id is None:
                    photo.size = os.path.getsize(file_path)
                    photo.extension = os.path.splitext(file_path)[1][1:]
                    photo.format = models.Photo.extension_to_format_key(photo.extension)

                    for key, val in helpers.extract_info(file_path).items():
                        setattr(photo, key, val)

                photo.deleted = False
    
                db.add(photo)

                file.photo = photo

                if (force or photo.id is None) and make_thumbnails:
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


def create_thumbnails(filename, thumbnails):
    with wand.image.Image(filename=filename) as im:
        for size, dest in thumbnails:
            logging.debug("Creating thumbnail %s from filename %s", dest, filename)
            with im.clone() as cl:
                cl.format = 'jpeg'
                cl.auto_orient()
                cl.resize(*helpers.resize_dimensions((cl.width, cl.height), size))
                cl.save(filename=dest)


