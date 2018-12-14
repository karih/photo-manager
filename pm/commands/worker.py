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

        dest_files = []

        sizes = [task['size'], ]  if 'size' in task else task['sizes']

        dest_files = [(size, file.get_path(size)) for size in sizes]
        dest_files = list(filter(lambda f: not os.path.exists(f[1]), dest_files))

        try:
            for size, file in dest_files:
                logger.info("Resizing size=%s dst=%50s src=%s", size, file, source_file)
            image_processing.create_thumbnails(source_file, 
                [(app.config["SIZES"][size][0:3], dest_file, ) for size, dest_file in dest_files]
            )
        except Exception as e:
            logger.exception("Exception while resizing photo")
