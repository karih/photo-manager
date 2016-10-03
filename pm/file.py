import os
import os.path
import logging
import datetime
import hashlib

import wand

from . import app, db, helpers, models


def scan_tree(make_thumbnails=False):
    for file_path in search_for_images(app.config["SEARCH_ROOT"]):
        processed = 0
        skipped = 0
        failed = 0

        try:
            if models.File.query.filter(models.File.path == file_path).count() < 1:
                logging.info("Processing %s", file_path)
                stat = os.stat(file_path)
                file = models.File(path=file_path, ctime=datetime.datetime.fromtimestamp(stat.st_ctime), deleted=False)
                try:

                    with open(file_path, 'rb') as f:
                        m = hashlib.sha512()
                        m.update(f.read())
                        hash = m.hexdigest()

                    photos = models.Photo.query.filter(models.Photo.hash == hash).all()
                    if len(photos) > 0:
                        photo = photos[0]
                    else:
                        size = os.path.getsize(file_path)
                        extension = os.path.splitext(file_path)[1][1:]

                        info = helpers.extract_info(file_path)

                        photo = models.Photo(
                            size=size, 
                            hash=hash, 
                            format=models.Photo.extension_to_format_key(extension),
                            **info
                        )
                        

                        db.add(photo)

                        if make_thumbnails and (not os.path.exists(photo.path_large) or not os.path.exists(photo.path_thumb)):
                            thumbs = [(app.config["LARGE_SIZE"], photo.path_large), (app.config["THUMB_SIZE"], photo.path_thumb)]

                            create_thumbnails(file_path, thumbs)

                            if app.config["SAVE_MASK"] is not None:
                                os.chmod(photo.path_large, app.config["SAVE_MASK"])
                                os.chmod(photo.path_thumb, app.config["SAVE_MASK"])
                            if app.config["SAVE_GROUP"] is not None:
                                os.chown(photo.path_large, -1, app.config["SAVE_GROUP"])
                                os.chown(photo.path_thumb, -1, app.config["SAVE_GROUP"])

                    file.photo = photo
                    
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


