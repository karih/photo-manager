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
    

    for pid in range(126000,166813+1):
        if pid % 100 == 0:
            print("========== Processed %d photos" % pid)
        photo = models.Photo.query.get(pid)

        if photo is None:
            try:
                es.delete(index=app.config["ELASTICSEARCH_INDEX"], doc_type="photo", id=pid)
            except elasticsearch.exceptions.NotFoundError:
                pass
            continue

        try:
            es.update(index=app.config["ELASTICSEARCH_INDEX"], doc_type="photo", id=photo.id, body={'doc': photo.get_document()})
        except elasticsearch.exceptions.NotFoundError:
            es.create(index=app.config["ELASTICSEARCH_INDEX"], doc_type="photo", id=photo.id, body=photo.get_document())

    sys.exit(0)




    idx = index.Index()
    idx.delete()
    idx.create()

    for photo in models.model_iterator(models.Photo.query):
        es.create(index=app.config["ELASTICSEARCH_INDEX"], doc_type="photo", id=photo.id, body=photo.get_document())

    sys.exit(0)
#
#            except es.NotFoundError as e:
#                pass
#        else:
#            for field in list(iter(documents.PhotoDocument._doc_type.mapping)):
#                if hasattr(photo, field):
#                    fields[field] = getattr(photo, field)
#
#            make, model = photo.make, photo.model
#            if make is None:
#                make = ""
#            if model is None:
#                model = ""
#
#            combined = ""
#            extract_brands = ("Nikon", "Canon", "Kodak", "Olympus", "Pentax", "Minolta", "Casio", "Fujifilm", "Sony")
#            for i in extract_brands:
#                if i.lower() in make.lower():
#                    make = i
#
#            if "hewlett" in make.lower():
#                make = "HP"
#
#            #if len(make) > 1:
#            #    make = make[0].upper() + make[1:].lower()
#
#            if model.lower().startswith(make.lower()):
#                model = model[len(make):].strip()
#
#
#            model = re.sub(u"zoom digital camera", "", model, flags=re.I).strip()
#            model = re.sub(u"digital camera$", "", model, flags=re.I).strip()
#            model = re.sub(u"digital$", "", model, flags=re.I).strip()
#
#            combined = ("%s %s" % (make, model)).strip()
#
#            fields["model"] = None if len(combined) < 1 else combined
#            fields["model_ci"] = None if len(combined) < 1 else combined
#            fields["lens_ci"] = photo.lens
#            fields["photo_id"] = photo.id
#            doc = documents.PhotoDocument(meta={'id' : photo.id}, **fields)
#            doc.save()
#
