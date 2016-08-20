# encoding=utf-8

import os
import logging
import datetime, calendar
import simplejson as json

from flask import Flask, render_template, jsonify
#from flask_sockets import Sockets
from gevent import Timeout, Greenlet, sleep

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", filename='flask.log', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().addHandler(logging.StreamHandler())

app = Flask(__name__)

if 'PM_CONFIG' in os.environ:
    app.config.from_envvar('PM_CONFIG')
else:
    app.config.from_object('pm.devconfig')


db_engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"], echo=False)
db_session = scoped_session(sessionmaker(bind=db_engine))
Base = declarative_base()
Base.query = db_session.query_property()

from . import models
from . import views
from . import api
