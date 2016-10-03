# encoding = utf-8

import re
import sys
import logging

from .. import models
from ..search import documents

def main(*args):
    """ Drops and rebuilds the elasticsearch index """

    documents.PhotoIndex.delete(ignore=404)
    documents.PhotoIndex.create(ignore=400)

    rows = models.Photo.query.count()
    logging.info("Total photo objects: %d" % rows)

    for offset in [x*1000 for x in range(rows//1000 + 1)]:
        logging.debug("Objects indexed %d", offset)
        for photo in models.Photo.query.offset(offset).limit(1000):
            fields = {}
            for field in list(iter(documents.PhotoDocument._doc_type.mapping)):
                if hasattr(photo, field):
                    fields[field] = getattr(photo, field)


            make, model = photo.make, photo.model
            if make is None:
                make = ""
            if model is None:
                model = ""

            combined = ""
            extract_brands = ("Nikon", "Canon", "Kodak", "Olympus", "Pentax", "Minolta", "Casio", "Fujifilm", "Sony")
            for i in extract_brands:
                if i.lower() in make.lower():
                    make = i

            if "hewlett" in make.lower():
                make = "HP"

            #if len(make) > 1:
            #    make = make[0].upper() + make[1:].lower()

            if model.lower().startswith(make.lower()):
                model = model[len(make):].strip()


            model = re.sub(u"zoom digital camera", "", model, flags=re.I).strip()
            model = re.sub(u"digital camera$", "", model, flags=re.I).strip()
            model = re.sub(u"digital$", "", model, flags=re.I).strip()

            combined = ("%s %s" % (make, model)).strip()

            fields["model"] = None if len(combined) < 1 else combined
            fields["model_ci"] = None if len(combined) < 1 else combined
            fields["lens_ci"] = photo.lens
            fields["photo_id"] = photo.id
            doc = documents.PhotoDocument(meta={'id' : photo.id}, **fields)
            doc.save()

