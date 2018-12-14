# encoding = utf-8

import os
import os.path
import json
import logging

from .. import redis, app
from .. import models
from .. import image_processing


logger = logging.getLogger(__name__)


def main(*args):
    while True:
        channel, task = redis.brpop('thumbnail-queue')
        task = json.loads(task)
        file = models.File.query.get(task['file_id'])
        source_file = file.path
        dest_file   = file.get_path(task['size'])
        if os.path.exists(dest_file):
            logger.info("Skipping dst=%30s size=%s dst=%s", dest_file, task["size"], source_file)
            continue
        else:
            logger.info("Resizing dst=%30s size=%s dst=%s", dest_file, task["size"], source_file)
        try:
            image_processing.create_thumbnails(source_file, [(app.config["SIZES"][task["size"]][0:3], dest_file, )])
        except Exception as e:
            logger.exception("Exception while resizing photo")
