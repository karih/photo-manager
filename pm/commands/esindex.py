# encoding = utf-8

from .. import models
from .. import documents

def main(*args):
    documents.photos.create(ignore=400)
    photos = models.Photo.query.all()

    import ipdb; ipdb.set_trace()

    for photo in photos:
        doc = documents.PhotoDocument(date=photo.date, aperture=photo.aperture, focal_length_35=photo.focal_length_35, iso=photo.iso, meta={'id' : photo.id})
        doc.save()

