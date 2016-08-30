import logging
import datetime
import os.path

from sqlalchemy import and_

from .. import db_session
from ..models import ImageFile, Photo


def main():
    for photo in Photo.query.filter(Photo.changed == None):
        for p in ("date", "aperture", "exposure", "focal_length", "focal_length_35", "iso", "make", "model", "lens"):
            values = [getattr(f, p) for f in photo.files if getattr(f, p) is not None]
            if len(values) > 0:
                setattr(photo, p, values[0])

    db_session.commit()


