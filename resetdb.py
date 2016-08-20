# encoding = utf-8

from pm import db_engine, Base
import pm.models

def db_drop_all():
    Base.metadata.drop_all(db_engine)

def db_create_all():
    Base.metadata.create_all(db_engine)

if __name__ == "__main__":
    db_drop_all()
    db_create_all()

