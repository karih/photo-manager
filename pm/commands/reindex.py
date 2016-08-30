# encoding = utf-8

import sys

from .. import models
from .. import documents

def main(*args):
    documents.photos.delete(ignore=404)
    documents.photos.create(ignore=400)
    photos = models.Photo.query.all()

    for photo in photos:
        fields = {}
        for field in list(iter(documents.PhotoDocument._doc_type.mapping)):
            fields[field] = getattr(photo, field)
        doc = documents.PhotoDocument(meta={'id' : photo.id}, **fields)
        doc.save()

