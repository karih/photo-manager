import os
import os.path
import logging

import wand

from . import app, helpers


def create_photo_thumbnails(photo):
    if not os.path.exists(photo.path_large) or not os.path.exists(photo.path_thumb):
        logging.debug("Creating thumbnails")
        thumbs = [(app.config["LARGE_SIZE"], photo.path_large), (app.config["THUMB_SIZE"], photo.path_thumb)]

        create_thumbnails(photo.paths[0], thumbs)

        if app.config["SAVE_MASK"] is not None:
            os.chmod(photo.path_large, app.config["SAVE_MASK"])
            os.chmod(photo.path_thumb, app.config["SAVE_MASK"])
        if app.config["SAVE_GROUP"] is not None:
            os.chown(photo.path_large, -1, app.config["SAVE_GROUP"])
            os.chown(photo.path_thumb, -1, app.config["SAVE_GROUP"])
    else:
        pass
        #logging.debug("Thumbnails exist")

def create_thumbnails(filename, thumbnails):
    """
        Give a `filename`, creates one or more thumbnails, as defined by the list
        `thumbnails` which should contains tuples ((`width`,`height`),`destination`)
    """

    with wand.image.Image(filename=filename) as im:
        for size, dest in thumbnails:
            logging.debug("Creating thumbnail %s from filename %s", dest, filename)
            with im.clone() as cl:
                cl.format = 'jpeg'
                cl.auto_orient()
                cl.resize(*helpers.resize_dimensions((cl.width, cl.height), size))
                cl.save(filename=dest)


