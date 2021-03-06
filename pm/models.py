# encoding=utf-8

import os
import hashlib
import shutil
import os.path
import datetime
import logging
import tempfile

import elasticsearch
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


def model_iterator(query, pre=None, post=None, limit=1000):
    rows = query.count()
    
    for offset in [x*limit for x in range(rows//limit + 1)]:
        if pre is not None:
            pre(offset=offset, limit=limit, rows=rows)
        for obj in query.offset(offset).limit(limit):
            yield obj
        if post is not None:
            post(offset=offset, limit=limit, rows=rows)


labels_association_table = sa.Table('labels_photos', Base.metadata,
    sa.Column('label_id', sa.Integer, sa.ForeignKey('labels.id')),
    sa.Column('photo_id', sa.Integer, sa.ForeignKey('photos.id'))
)
photo_file_association_table = sa.Table('photo_files', Base.metadata,
    sa.Column('photo_id', sa.Integer, sa.ForeignKey('photos.id')),
    sa.Column('file_id',  sa.Integer, sa.ForeignKey('files.id'))
)


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    username   = sa.Column(sa.String(1000), nullable=False, unique=True)
    password   = sa.Column(sa.String(1000), nullable=True)
    #totp       = sa.Column(sa.String(1000), nullable=True)
    admin      = sa.Column(sa.Boolean, default=False)
    system_uid = sa.Column(sa.Integer, nullable=True, index=True, unique=True)

    last_movement       = sa.Column(sa.DateTime, nullable=True)
    last_authentication = sa.Column(sa.DateTime, nullable=True)
    last_pw_change      = sa.Column(sa.DateTime, nullable=True)

    #files    = relationship("File", back_populates="users", secondary=user_files_association_table)
    source_files = relationship("SourceFile", back_populates="owner")
    photos       = relationship("Photo",      back_populates="owner")
    labels       = relationship("Label",      back_populates="owner")
    sessions     = relationship("Session",    back_populates="user")

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

    @classmethod
    def sync_system_passwd(cls, min_uid=1000, max_uid=49999):
        import pwd
        users = [user for user in pwd.getpwall() if user.pw_uid >= min_uid and user.pw_uid <= max_uid]
        created = []
        for user_entry in users:
            try:
                user = cls(username=user_entry.pw_name, system_uid=user_entry.pw_uid)
                db.add(user)
                db.commit()
                created.append(user)
            except:
                db.rollback()

        return created


class Session(Base):
    __tablename__ = 'session'

    id  = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String(1000), nullable=False, unique=True)
    
    created = sa.Column(sa.DateTime, nullable=False)
    expires = sa.Column(sa.DateTime, nullable=False)
    active_flag = sa.Column(sa.Boolean, default=False, nullable=False)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="sessions")

    @classmethod
    def get_session(cls, session_key):
        session = cls.query.filter(cls.key == session_key)\
            .filter(cls.active_flag==True)\
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
            active_flag=True,
            user=user,
            created=datetime.datetime.now(),
            expires=datetime.datetime.now()+datetime.timedelta(days=7)
        )
        db.add(session)
        db.commit()
        return session

    def destroy(self):
        self.active_flag=False
        db.commit()


class SourceFile(Base):
    """ 
        This table lists individual files in the file system.
        Identical files (as determined by the file hash) are grouped together through `File`
    """

    __tablename__ = 'source_files'

    id         = sa.Column(sa.Integer,      primary_key=True)
    ctime      = sa.Column(sa.DateTime,     nullable=False)
    path       = sa.Column(sa.String(1000), nullable=False, index=True, unique=True)
    first_scan = sa.Column(sa.DateTime,     server_default=func.now()) # datetime of first file discovery
    last_scan  = sa.Column(sa.DateTime,     server_default=func.now()) # datetime of last file discovery
    deleted    = sa.Column(sa.Boolean,      nullable=False, server_default='f', default=False) 
    inode      = sa.Column(sa.Integer,      nullable=False) # inode in the particular filesystem
    device     = sa.Column(sa.Numeric(precision=24, scale=0), nullable=False) # the device id as reported by the OS - right now this is a combination of the major/minor number which can change across reboots

    disk_size  = sa.Column(sa.BigInteger, nullable=False) # stat.st_blocks * 512 -- https://docs.python.org/3/library/os.html#os.stat_result.st_blocks

    owner_id   = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    owner      = relationship("User",  back_populates="source_files")

    file_id    = sa.Column(sa.Integer, sa.ForeignKey('files.id'), nullable=False)
    file       = relationship("File",  back_populates="source_files")

    @property
    def basename(self):
        return os.path.basename(self.path)
    
    @property
    def dirname(self):
        return os.path.dirname(self.path)

    @property
    def extension(self):
        return self.path.split(".")[-1]

    @property
    def format(self):
        return self.extension_to_format_key(self.extension)

    @staticmethod
    def extension_to_format_key(ext):
        for i, (format, extensions) in enumerate(FORMAT_EXTENSIONS):
            if ext.lower() in extensions:
                return i
        raise ValueError("Unknown extension %s" % ext)

    def update_last_scan(self):
        self.last_scan = func.now()


metadata = dict(
    date            = sa.Column(sa.DateTime,     nullable=True), # exif timestamp
    aperture        = sa.Column(sa.Float,        nullable=True),
    exposure        = sa.Column(sa.Float,        nullable=True),
    focal_length    = sa.Column(sa.Float,        nullable=True),
    focal_length_35 = sa.Column(sa.Float,        nullable=True),
    iso             = sa.Column(sa.Integer,      nullable=True),
    make            = sa.Column(sa.String(128),  nullable=True),
    model           = sa.Column(sa.String(128),  nullable=True),
    orientation     = sa.Column(sa.SmallInteger, nullable=True),
    lens            = sa.Column(sa.String(128),  nullable=True),
    program         = sa.Column(sa.Integer,      nullable=True), # Aperture-priority/speed-priority/manual etc.
    exposure_mode   = sa.Column(sa.Integer,      nullable=True),
    release_mode    = sa.Column(sa.Integer,      nullable=True), # burst, bracketing, etc
    sequence_number = sa.Column(sa.Integer,      nullable=True), # burst sequence number
)


PhotoMetadataMixin            = type('PhotoMetadataMixin',            (object, ), metadata)
PhotoMetadataWithChangesMixin = type('PhotoMetadataWithChangesMixin', (object, ), {**metadata, **{("%s_changed" % k): sa.Column(sa.DateTime, nullable=True) for k in metadata.keys()}})


class File(PhotoMetadataMixin, Base):
    __tablename__ = 'files'

    FORMATS = [x[0] for x in FORMAT_EXTENSIONS]

    id = sa.Column(sa.Integer, primary_key=True)

    hash      = sa.Column(sa.String(128), nullable=False, index=True, unique=True) # sha512 hexdigest
    file_size = sa.Column(sa.BigInteger,  nullable=False) # stat.st_size -- https://docs.python.org/3/library/os.html#os.stat_result.st_size 
    source_files = relationship("SourceFile", back_populates="file")
    photos       = relationship("Photo",      secondary=photo_file_association_table, back_populates="files", lazy='dynamic')

    # METADATA
    width  = sa.Column(sa.Integer, nullable=True)
    height = sa.Column(sa.Integer, nullable=True)

    def get_path(self, size):
        hash = m = hashlib.sha256()
        hash.update(self.hash.encode('utf-8'))
        hash.update((":".join(map(str, app.config['SIZES'][size]))).encode('utf-8'))

        return os.path.join(app.config['TEMP_DIR'], "files", hash.hexdigest()[:3], 'file_%s.jpg' % hash.hexdigest()[:30])




class Photo(PhotoMetadataWithChangesMixin, Base):
    """ 
        All information in this table is extracted from the image file itself,
        none of it is editable in any interface.
        This is an object that groups different files that correspond to the same photo (same shutter opening),
        for example, if there exists a jpg and raw edition of the photo they will only have one Photo object.
    """
    __tablename__ = 'photos'

    id = sa.Column(sa.Integer, primary_key=True)

    # was any of the information manually changed
    changed = sa.Column(sa.DateTime, nullable=True)
    hidden  = sa.Column(sa.Boolean,  nullable=False, default=False)
    deleted = sa.Column(sa.Boolean,  nullable=False, default=False)

    ### foreign keys
    # here while ordering we prioritize jpg and png above raw photos (for reduced thumbnailing load)
    #files = relationship("File", back_populates="photo", order_by=[sa.case(
    #    [ 
    #        ( sa.func.lower(sa.func.substr(File.path, sa.func.length(File.path)-2, sa.func.length(File.path))) == "jpg", 0),
    #        ( sa.func.lower(sa.func.substr(File.path, sa.func.length(File.path)-3, sa.func.length(File.path))) == "jpeg", 0),
    #        ( sa.func.lower(sa.func.substr(File.path, sa.func.length(File.path)-2, sa.func.length(File.path))) == "png", 1),
    #    ], else_=2
    #), sa.desc(File.size), sa.asc(File.id)])
    files = relationship("File", secondary=photo_file_association_table, back_populates="photos")

    group_id   = sa.Column(sa.Integer, sa.ForeignKey('groups.id'), nullable=True )
    owner_id   = sa.Column(sa.Integer, sa.ForeignKey('users.id'),  nullable=False)
    group      = relationship("Group", back_populates="photos")
    owner      = relationship("User",  back_populates="photos")

    #people = relationship("Person", secondary=people_association_table, back_populates="photos")
    labels = relationship("Label", secondary=labels_association_table, back_populates="photos")

    @property
    def source_files(self):
        return [f for file in self.files for f in file.source_files if f.owner == self.owner and not f.deleted]

    __document_name__ = "photo"
    __document__ = {
        "properties": {
            "photo_id":        {"type": "integer" },
            "paths":           {"type": "keyword" }, 
            "basenames":       {"type": "keyword" }, 
            "dirnames":        {"type": "keyword" }, 
            "date":            {"type": "date" }, 
            "label":           {"type": "keyword" },
            "label_ids":       {"type": "integer" },
            "year":            {"type": "integer" },
            "month":           {"type": "integer" },
            "path_components": {"type": "text" },
            #"file_id":         {"type": "integer" },
            #"aperture":        { "type": "float" }, 
            #"exposure":        { "type": "float" }, 
            #"model":           { "type": "text", "index": "not_analyzed" }, 
            #"iso":             { "type": "integer" }, 
            #"lens":            { "type": "text", "index": "not_analyzed" }, 
            #"focal_length":    { "type": "float" }, 
            #"focal_length_35": { "type": "float" }, 
            #"size":            { "type": "integer" },
            #"users":           { "type": "integer" }
        }
    }


    @property
    def paths(self):
        return [f.path for f in self.source_files]

    @property
    def basenames(self):
        return sorted(list(set([f.basename for f in self.source_files])))

    @property
    def dirnames(self):
        return sorted(list(set([f.dirname for f in self.source_files])))

    def get_document(self):
        return {
            'id': self.id,
            'date': self.date,
            #'dirnames': self.dirnames,
            #'basenames': self.basenames,
            #'paths': self.paths,
            #'file_id': self.files[0].id if len(self.files) > 0 else None,
            'label': [lbl.label for lbl in self.labels],
            'label_ids': [lbl.id for lbl in self.labels],
            #'path_components': " ".join([seg for path in self.paths for seg in path.split("/")]),
            'year': self.date.year if self.date is not None else None,
            'month': self.date.month if self.date is not None else None,
        }
        #fields = ('width', 'height', 'date', 'dirnames', 'model', 'lens')
        #return {k: getattr(self, k) for k in fields}

    def merge(self, photo):
        for file in photo.files:
            self.files.append(file)

        for labels in photo.labels:
            self.labels.append(labels)

        if photo.group:
            assert self.group is None
            self.group = photo.group

        photo.labels = []
        photo.files  = []
#
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
#
#

class Group(Base):
    ''' 
        Group() is an entity corresponding to a single shutter press.
        Can be a bracketing group or a continuous burst shot, or possibly something else?
    '''
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

class Label(Base):
    __tablename__ = "labels"

    id = sa.Column(sa.Integer, primary_key=True)
    label = sa.Column(sa.Unicode(255), nullable=False)

    owner_id   = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    owner      = relationship("User",  back_populates="labels")

    photos = relationship("Photo", secondary=labels_association_table, back_populates="labels")


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
        if type == 0:
            es.create(index=app.config["ELASTICSEARCH_INDEX"], doc_type=target.__document_name__, id=target.id, body=target.get_document())
        elif type == 1:
            try:
                es.update(index=app.config["ELASTICSEARCH_INDEX"], doc_type=target.__document_name__, id=target.id, body={'doc' : target.get_document()})
            except elasticsearch.exceptions.NotFoundError:
                es.create(index=app.config["ELASTICSEARCH_INDEX"], doc_type=target.__document_name__, id=target.id, body=target.get_document())
        else:
            es.delete(index=app.config["ELASTICSEARCH_INDEX"], doc_type=target.__document_name__, id=target.id)
    return inner

event.listen(Photo, 'after_insert', photo_event(0))
event.listen(Photo, 'after_update', photo_event(1))
event.listen(Photo, 'after_delete', photo_event(2))

#event.listen(Group, 'after_delete', photo_deleted)
#event.listen(Group, 'after_insert', photo_deleted)
#event.listen(Group, 'after_update', photo_deleted)
