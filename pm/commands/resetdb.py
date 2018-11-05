# encoding = utf-8

import logging

from .. import db_engine, Base
from .. import models
from . import user


logger = logging.getLogger(__name__)


def db_drop_all():
    Base.metadata.drop_all(db_engine)

def db_create_all():
    Base.metadata.create_all(db_engine)

def main(*args):
    print("Dropped all database objects")
    db_drop_all()
    print("Initialized database")
    db_create_all()
    print("Created user admin with password admin")
    user.add_user(["admin", "admin"])


