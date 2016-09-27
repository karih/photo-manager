import logging
import datetime
import os.path

from sqlalchemy import and_

from .. import db_session
from ..models import ImageFile, Photo


def main():
    # to avoid potential memory problems:
    # https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/WindowedRangeQuery

    rows = ImageFile.query.filter(ImageFile.photo == None).count()
    logging.info("Rows without assigned photo: %d" % rows)

    for offset in [x*1000 for x in range(rows//1000+1)]:
        logging.debug("Rows processed: %d" % offset)
        for image in ImageFile.query.filter(ImageFile.photo == None).offset(offset).limit(1000):
            # check for an image with the same hash - in which case they are identical
            res = ImageFile.query.filter(ImageFile.photo_id != None).filter(ImageFile.hash == image.hash).all()

            if len(set([i.photo_id for i in res])) > 1:
                logging.warning("Distinct files with equal hash %s have separate photo connections: %s", image.hash, [i.photo_id for i in res])

            if len(res) > 0:
                image.photo = res[0].photo
                db_session.commit()
                continue
            
            # next step, check for file with same basename (minus extension) and same date
            query = ImageFile.query.filter(ImageFile.photo_id != None).filter(ImageFile.path.like('%%%s%%' % os.path.splitext(image.basename)[0]))

            if image.date is not None:
                res = query.filter(ImageFile.date == image.date).all()

                if len(res) > 0:
                    logging.warning("Assigning similarities based on filename (%s, %s) and date (%s, %s)", image.path, res[0].path, image.date, res[0].date)
                    image.photo = res[0].photo
                    db_session.commit()
                    continue

            # create a new photo object
            photo = Photo()
            photo.file = image
            db_session.add(photo)
            db_session.commit()
            image.photo = photo
            db_session.commit()
