# encoding = utf-8

import re
import sys
import logging

import elasticsearch

from .. import app, es
from .. import models
from ..search import index

def main(*args):
    """ Drops and rebuilds the elasticsearch index """

    idx = index.Index()
    idx.delete()
    idx.create()

    for photo in models.model_iterator(models.Photo.query):
        es.create(index=app.config["ELASTICSEARCH_INDEX"], doc_type="photo", id=photo.id, body=photo.get_document())

