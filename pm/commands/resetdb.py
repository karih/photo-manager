# encoding = utf-8

from .. import db_engine, Base
from .. import models

def db_drop_all():
    Base.metadata.drop_all(db_engine)

def db_create_all():
    Base.metadata.create_all(db_engine)

def main(*args):
    db_drop_all()
    db_create_all()

