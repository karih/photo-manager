import logging

from .. import db, models

def get_photo_batch_iterator():
    rows = models.Photo.query.count()
    logging.info("Total photo objects: %d" % rows)

    for offset in [x*1000 for x in range(rows//1000 + 1)]:
        logging.debug("Objects indexed: %d", offset)
        for photo in models.Photo.query.offset(offset).limit(1000):
            yield photo

        db.commit()
            
    logging.info("Objects processed: %d", rows)
