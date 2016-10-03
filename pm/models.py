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

from . import app, Base, helpers


class File(Base):
    __tablename__ = 'files'

    id = sa.Column(sa.Integer, primary_key=True)
    ctime = sa.Column(sa.DateTime, nullable=False)
    path = sa.Column(sa.String(1000), nullable=False, unique=True)
    scanned = sa.Column(sa.DateTime, server_default=func.now()) # datetime of file discovery
    error = sa.Column(sa.Text, nullable=True) 
    deleted = sa.Column(sa.Boolean, nullable=False) 

    photo_id = sa.Column(sa.Integer, sa.ForeignKey('photos.id'), nullable=True)
    photo = relationship("Photo", back_populates="files")

    @property
    def basename(self):
        return os.path.basename(self.path)
    
    @property
    def dirname(self):
        return os.path.dirname(self.path)


people_association_table = sa.Table('people_photos', Base.metadata,
    sa.Column('people_id', sa.Integer, sa.ForeignKey('people.id')),
    sa.Column('photo_id', sa.Integer, sa.ForeignKey('photos.id'))
)


labels_association_table = sa.Table('labels_photos', Base.metadata,
    sa.Column('label_id', sa.Integer, sa.ForeignKey('labels.id')),
    sa.Column('photo_id', sa.Integer, sa.ForeignKey('photos.id'))
)


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


class Photo(Base):
    """ All information in this table is extracted from the image file itself,
        none if it is editable in any interface.
    """
    __tablename__ = 'photos'

    FORMATS = [x[0] for x in FORMAT_EXTENSIONS]

    id = sa.Column(sa.Integer, primary_key=True)
    size = sa.Column(sa.Integer, nullable=False)
    hash = sa.Column(sa.String(128), nullable=False) # sha512 hexdigest
    width = sa.Column(sa.SmallInteger, nullable=False)
    height = sa.Column(sa.SmallInteger, nullable=False)
    format = sa.Column(sa.SmallInteger, nullable=False)

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

    # foreign keys
    files = relationship("File", back_populates="photo")

    group_id = sa.Column(sa.Integer, sa.ForeignKey('groups.id'), nullable=True)
    group = relationship("Group", back_populates="photos")

    people = relationship("Person", secondary=people_association_table, back_populates="photos")
    labels = relationship("Label", secondary=labels_association_table, back_populates="photos")

    #primaries = relationship("Photo", back_populates="file", foreign_keys="Photo.file_id")
    #derivatives = relationship('PhotoDerivative', back_populates='orig')

    
    @staticmethod
    def extension_to_format_key(ext):
        for i, (format, extensions) in enumerate(FORMAT_EXTENSIONS):
            if ext.lower() in extensions:
                return i
        raise ValueError("Unknown extension %s" % ext)

    @property
    def path_thumb(self):
        actual_size = helpers.resize_dimensions((self.width, self.height), app.config["THUMB_SIZE"]) 
        return os.path.join(app.config['TEMP_DIR'], "%s_%d_%d.jpg" % (self.hash, actual_size[0], actual_size[1]))

    @property
    def path_large(self):
        actual_size = helpers.resize_dimensions((self.width, self.height), app.config["LARGE_SIZE"]) 
        return os.path.join(app.config['TEMP_DIR'], "%s_%d_%d.jpg" % (self.hash, actual_size[0], actual_size[1]))

    @property
    def path(self):
        return [f.path for f in self.files]

    @property
    def basename(self):
        return sorted(list(set([f.basename for f in self.files])))

    @property
    def dirname(self):
        return sorted(list(set([f.dirname for f in self.files])))

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
        they are all linked to this single photo. '''
    __tablename__ = 'groups'
        
    id = sa.Column(sa.Integer, primary_key=True)

    photos = relationship("Photo", back_populates="group")


    def merge(self, group):
        for photo in group.photos:
            self.photos.append(photo)


class Person(Base):
    __tablename__ = "people"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(255), nullable=False)

    photos = relationship("Photo", secondary=people_association_table, back_populates="people")


class Label(Base):
    __tablename__ = "labels"

    id = sa.Column(sa.Integer, primary_key=True)
    label = sa.Column(sa.Unicode(255), nullable=False)

    photos = relationship("Photo", secondary=labels_association_table, back_populates="labels")


#class PhotoDerivative(Base):
#    __tablename__ = 'derivatives'
#
#    id = sa.Column(sa.Integer, primary_key=True)
#
#    photo_id = sa.Column(sa.Integer, sa.ForeignKey('photos.id'), nullable=False)
#    photo = relationship('Photos', back_populates='derivatives')
