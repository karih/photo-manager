# encoding=utf-8

import os
import hashlib
import shutil
import os.path
import datetime
import logging
import tempfile

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, HSTORE, JSON
from sqlalchemy.sql import func
from sqlalchemy import event

from . import app, db, Base, helpers, es

FORMAT_EXTENSIONS = (
    ('JPG', ('jpg', 'jpeg')), 
    ('PNG', ('png', )),
    ('NEF', ('nef', )),
    ('CR2', ('cr2', )),
    ('CRW', ('crw', )),
    ('ARW', ('arw', )),
    ('SRF', ('srf', )),
    ('SR2', ('sr2', ))
)


def model_iterator(query, pre=None, post=None):
    rows = query.count()
    limit = 1000
    
    for offset in [x*limit for x in range(rows//limit + 1)]:
        if pre is not None:
            pre(offset=offset, limit=limit, rows=rows)
        for obj in query.offset(offset).limit(limit):
            yield obj
        if post is not None:
            post(offset=offset, limit=limit, rows=rows)


user_files_association_table = sa.Table('users_files', Base.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
    sa.Column('file_id', sa.Integer, sa.ForeignKey('files.id'))
)


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(1000), nullable=False, unique=True)
    password = sa.Column(sa.String(1000), nullable=False)
    totp = sa.Column(sa.String(1000), nullable=True)
    admin = sa.Column(sa.Boolean, default=False, nullable=True)

    last_movement       = sa.Column(sa.DateTime, nullable=True)
    last_authentication = sa.Column(sa.DateTime, nullable=True)
    last_pw_change      = sa.Column(sa.DateTime, nullable=True)

    files = relationship("File", back_populates="users", secondary=user_files_association_table)
    sessions = relationship("Session", back_populates="user")

    def set_password(self, password):
        from passlib.hash import scrypt
        self.password = scrypt.hash(password)

    def verify_password(self, password):
        from passlib.hash import scrypt
        return scrypt.verify(password, self.password)

    @classmethod
    def authenticate(cls, username, password):
        user = cls.query.filter(cls.username==username).first()
        if user.verify_password(password):
            return user
        else:
            raise ValueError("Invalid username/password combination")


class Session(Base):
    __tablename__ = 'session'

    id  = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String(1000), nullable=False, unique=True)
    
    created = sa.Column(sa.DateTime, nullable=False)
    expires = sa.Column(sa.DateTime, nullable=False)
    active = sa.Column(sa.Boolean, default=False, nullable=False)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="sessions")

    @classmethod
    def get_session(cls, session_key):
        session = cls.query.filter(cls.key == session_key)\
            .filter(cls.active==True)\
            .filter(cls.created<=datetime.datetime.now())\
            .filter(cls.expires>=datetime.datetime.now()).first()
        if session is not None:
            return session
        else:
            raise ValueError("No such session %s" % session_key)

    @classmethod
    def create_session(cls, user):
        import uuid
        session = Session(
            key=str(uuid.uuid4()),
            active=True,
            user=user,
            created=datetime.datetime.now(),
            expires=datetime.datetime.now()+datetime.timedelta(days=7)
        )
        db.add(session)
        db.commit()
        return session

    def destroy(self):
        self.active=False
        db.commit()


class File(Base):
    __tablename__ = 'files'

    FORMATS = [x[0] for x in FORMAT_EXTENSIONS]

    id = sa.Column(sa.Integer, primary_key=True)
    ctime = sa.Column(sa.DateTime, nullable=False)
    path = sa.Column(sa.String(1000), nullable=False, unique=True)
    scanned = sa.Column(sa.DateTime, server_default=func.now()) # datetime of file discovery
    error = sa.Column(sa.Text, nullable=True) 
    deleted = sa.Column(sa.Boolean, nullable=False, server_default='f', default=False) 

    hash = sa.Column(sa.String(128), nullable=False) # sha512 hexdigest
    format = sa.Column(sa.SmallInteger, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)

    photo_id = sa.Column(sa.Integer, sa.ForeignKey('photos.id'), nullable=True)
    photo = relationship("Photo", back_populates="files")

    users = relationship("User", back_populates="files", secondary=user_files_association_table)

    @property
    def basename(self):
        return os.path.basename(self.path)
    
    @property
    def dirname(self):
        return os.path.dirname(self.path)

    @staticmethod
    def extension_to_format_key(ext):
        for i, (format, extensions) in enumerate(FORMAT_EXTENSIONS):
            if ext.lower() in extensions:
                return i
        raise ValueError("Unknown extension %s" % ext)




#people_association_table = sa.Table('people_photos', Base.metadata,
#    sa.Column('people_id', sa.Integer, sa.ForeignKey('people.id')),
#    sa.Column('photo_id', sa.Integer, sa.ForeignKey('photos.id'))
#)
#
#
#labels_association_table = sa.Table('labels_photos', Base.metadata,
#    sa.Column('label_id', sa.Integer, sa.ForeignKey('labels.id')),
#    sa.Column('photo_id', sa.Integer, sa.ForeignKey('photos.id'))
#)


class Photo(Base):
    """ All information in this table is extracted from the image file itself,
        none of it is editable in any interface.
        This is an object that groups different files that correspond to the same photo,
        if there exists a jpg and raw edition of the photo they will only have one Photo object.
    """
    __tablename__ = 'photos'

    id = sa.Column(sa.Integer, primary_key=True)
    width = sa.Column(sa.SmallInteger, nullable=False)
    height = sa.Column(sa.SmallInteger, nullable=False)

    # most important exif data
    date = sa.Column(sa.DateTime, nullable=True) # exif timestamp
    aperture = sa.Column(sa.Float, nullable=True)
    exposure = sa.Column(sa.Float, nullable=True)
    focal_length = sa.Column(sa.Float, nullable=True)
    focal_length_35 = sa.Column(sa.Float, nullable=True)
    iso = sa.Column(sa.Integer, nullable=True)
    make = sa.Column(sa.String(128), nullable=True)
    model = sa.Column(sa.String(128), nullable=True)
    orientation = sa.Column(sa.SmallInteger, nullable=True)

    # other exif stuff
    lens = sa.Column(sa.String(128), nullable=True)
    program = sa.Column(sa.Integer, nullable=True) # Aperture-priority/speed-priority/manual etc.
    exposure_mode = sa.Column(sa.Integer, nullable=True)
    release_mode = sa.Column(sa.Integer, nullable=True) # burst, bracketing, etc
    sequence_number = sa.Column(sa.Integer, nullable=True) # burst sequence number

    # was any of the information manually changed
    changed = sa.Column(sa.DateTime, nullable=True)
    hidden = sa.Column(sa.Boolean, nullable=False, default=False)
    deleted = sa.Column(sa.Boolean, nullable=False, default=False)

    ### foreign keys
    # here the ordering ensures the non-raw images are first (with lowest format number)
    files = relationship("File", back_populates="photo", order_by="File.format")

    group_id = sa.Column(sa.Integer, sa.ForeignKey('groups.id'), nullable=True)
    group = relationship("Group", back_populates="photos")

    #people = relationship("Person", secondary=people_association_table, back_populates="photos")
    #labels = relationship("Label", secondary=labels_association_table, back_populates="photos")

    #primaries = relationship("Photo", back_populates="file", foreign_keys="Photo.file_id")
    #derivatives = relationship('PhotoDerivative', back_populates='orig')

    __document_name__ = "photo"
    __document__ = {
        "properties": {
            "aperture": { "type": "float" }, 
            "path": { "type": "string", "index": "not_analyzed" }, 
            "date": { "type": "date" }, 
            "basenames": { "type": "string", "index": "not_analyzed" }, 
            "dirnames": { "type": "string", "index": "not_analyzed" }, 
            "exposure": { "type": "float" }, 
            "model": { "type": "string", "index": "not_analyzed" }, 
            "iso": { "type": "integer" }, 
            "lens": { "type": "string", "index": "not_analyzed" }, 
            "focal_length": { "type": "float" }, 
            "focal_length_35": { "type": "float" }, 
            "size": { "type": "integer" },
            "users": { "type": "integer" }
        }
    }

    @property
    def path_thumb(self):
        actual_size = helpers.resize_dimensions((self.width, self.height), app.config["THUMB_SIZE"]) 
        return os.path.join(app.config['TEMP_DIR'], "%s_%d_%d.jpg" % (self.files[0].hash, actual_size[0], actual_size[1]))

    @property
    def path_large(self):
        actual_size = helpers.resize_dimensions((self.width, self.height), app.config["LARGE_SIZE"]) 
        return os.path.join(app.config['TEMP_DIR'], "%s_%d_%d.jpg" % (self.files[0].hash, actual_size[0], actual_size[1]))

    @property
    def paths(self):
        return [f.path for f in self.files if f.deleted is False]

    @property
    def basenames(self):
        return sorted(list(set([f.basename for f in self.files])))

    @property
    def dirnames(self):
        return sorted(list(set([f.dirname for f in self.files])))

    def get_document(self):
        fields = ('width', 'height', 'date', 'dirnames', 'model', 'lens')
        return {k: getattr(self, k) for k in fields}

#    def dct(self):
#        return {
#            'id' : self.id,
#            'size' : self.size,
#            'width' : self.width,
#            'height' : self.height,
#            'ctime' : self.ctime,
#            'filename' : self.basename, 
#            'dirname' : os.path.dirname(self.path),
#            'date' : self.date,
#            'aperture': self.aperture,
#            'exposure' : self.exposure,
#            'focal_length' : self.focal_length,
#            'focal_length_35' : self.focal_length_35,
#            'iso' : self.iso,
#            'orientation' : self.orientation,
#            'make' : self.make,
#            'model' : self.model,
#            'lens' : self.lens
#        }


class Group(Base):
    ''' Group() is an entity corresponding to a single photo.
        If several versions of a photo exists, for example due to post processing
        they are all linked to this single group. '''
    __tablename__ = 'groups'
        
    id = sa.Column(sa.Integer, primary_key=True)

    photos = relationship("Photo", back_populates="group")

    def merge(self, group):
        for photo in group.photos:
            self.photos.append(photo)


#class Person(Base):
#    __tablename__ = "people"
#
#    id = sa.Column(sa.Integer, primary_key=True)
#    name = sa.Column(sa.Unicode(255), nullable=False)
#
#    photos = relationship("Photo", secondary=people_association_table, back_populates="people")
#
#
#class Label(Base):
#    __tablename__ = "labels"
#
#    id = sa.Column(sa.Integer, primary_key=True)
#    label = sa.Column(sa.Unicode(255), nullable=False)
#
#    photos = relationship("Photo", secondary=labels_association_table, back_populates="labels")


#class PhotoDerivative(Base):
#    __tablename__ = 'derivatives'
#
#    id = sa.Column(sa.Integer, primary_key=True)
#
#    photo_id = sa.Column(sa.Integer, sa.ForeignKey('photos.id'), nullable=False)
#    photo = relationship('Photos', back_populates='derivatives')


### EVENTS
def photo_event(type):
    def inner(mapper, connection, target):
        if type in (0, 1):
            (es.index if type == 1 else es.create)(index=app.config["ELASTICSEARCH_INDEX"], doc_type=target.__document_name__, id=target.id, body=target.get_document())
        else:
            es.delete(index=app.config["ELASTICSEARCH_INDEX"], doc_type=target.__document_name__, id=target.id)
    return inner

event.listen(Photo, 'after_insert', photo_event(0))
event.listen(Photo, 'after_update', photo_event(1))
event.listen(Photo, 'after_delete', photo_event(2))

#event.listen(Group, 'after_delete', photo_deleted)
#event.listen(Group, 'after_insert', photo_deleted)
#event.listen(Group, 'after_update', photo_deleted)
