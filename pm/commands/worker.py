# encoding = utf-8

import os
import os.path
import json
import logging
import random
import time

from .. import redis, app, logger
from .. import models
from .. import image_processing

from .. import tasks


def main(*args):
    _tasks = tasks.tasks
    
    # it is possible we instead want to do some sort of blocking pop 
    # possibly subscribe to some channel about new objects
    idle_iterations = 0
    while True:
        ran = 0
        for task_cls in sorted(_tasks.values(), key=lambda x: x.priority):
            task = task_cls.pop()
            if task is not None:
                logger.info("Executing task %s", task)
                task.execute()
                ran += 1
                continue
        if ran == 0:
            if idle_iterations % 100 == 0:
                logger.debug("Worker slept for %d iterations", idle_iterations)
            idle_iterations += 1
            time.sleep(0.1)
        else:
            idle_iterations = 0

        #channel, task = redis.brpop('thumbnail-queue')

        #task = json.loads(task)
        #file = models.File.query.get(task['file_id'])
        #source_file = file.path

        #dest_files = []

        #sizes = [task['size'], ]  if 'size' in task else task['sizes']

        #dest_files = [(size, file.get_path(size)) for size in sizes]
        #dest_files = list(filter(lambda f: not os.path.exists(f[1]), dest_files))

        #try:
        #    for size, file in dest_files:
        #        logger.info("Resizing size=%s dst=%50s src=%s", size, file, source_file)
        #    image_processing.create_thumbnails(source_file, 
        #        [(app.config["SIZES"][size][0:3], dest_file, ) for size, dest_file in dest_files]
        #    )
        #except Exception as e:
        #    logger.exception("Exception while resizing photo")
