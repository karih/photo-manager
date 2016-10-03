import logging
import datetime
import os.path

from sqlalchemy import and_

from .. import db
from ..models import File, Photo, Group


def main():
    # to avoid potential memory problems:
    # https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/WindowedRangeQuery

    rows = Photo.query.filter(Photo.group == None).count()

    for offset in [x*1000 for x in range(rows//1000+1)]:
        logging.debug("Rows processed: %d" % offset)
        for photo in Photo.query.filter(Photo.group == None).offset(offset).limit(1000):


            # check for file with same basename (minus extension) and same date
            if photo.date is not None:
                filenames = [file.basename for file in photo.files]

                res = set()
                for filename in filenames:
                    q = Photo.query.join(Photo.files).filter(File.path.like('%%/%s.%%' % os.path.splitext(filename)[0])).filter(Photo.date == photo.date).filter(Photo.id != photo.id)
                    res.update(q.all())


                res = list(res)
                    
                if len(res) > 0:
                    logging.warning("Assigning similarities based on filename (%s, %s) and date (%s)", filenames, res[0].files[0].path, photo.date)
                    if photo.group is not None:
                        photo.group = res[0].group 
                    else:
                        g = Group()
                        res[0].group = g
                        photo.group = g
                        db.add(g)
                    db.commit()

            # detect continuous shooting and group

            # detect bracketing and group
