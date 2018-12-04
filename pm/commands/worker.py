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
            continue
        
        logger.info("Resizing src=%s dst=%s to size %s", source_file, dest_file, task["size"])
        image_processing.create_thumbnails(source_file, [(app.config["SIZES"][task["size"]][0:2], dest_file, )])
