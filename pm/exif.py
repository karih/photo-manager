# encoding: utf-8

import os, sys
import os.path
import datetime
import logging
import subprocess
import json

import flask

from wand.image import Image

INFO = {
    "width" : None,
    "height" : None,
    "date" : None,
    "aperture" : None,
    "exposure" : None,
    "focal_length" : None,
    "focal_length_35" : None,
    "iso" : None,
    "make" : None,
    "model" : None,
    "orientation" : None,
    "lens" : None,
    "program" : None,
    "exposure_mode": None,
    "release_mode": None,
    "sequence_number": None, 

}

def aperture_parse(v):
    if isinstance(v, (float, int)):
        return float(v)
    elif v[0:2].lower() == "f/":
        return float(v[2:])
    elif v[0].lower() == "f":
        return float(v[1:])
    elif "/" in v:
        x, y = v.split("/")
        return float(x)/int(y)
    else:
        return float(v)

def exposure_parse(v):
    if isinstance(v, (float, int)):
        return float(v)
    else:
        if " " in v:
            v = v.split(" ")[0]

        if "/" in v:
            x, y = v.split("/")
            return float(x) / int(y)
        else:
            return float(v)

def focal_parse(v):
    if isinstance(v, (float, int)):
        return float(v)
    else:
        if " " in v:
            v = v.split(" ")[0]

        if "/" in v:
            x, y = v.split("/")
            return float(x) / int(y)
        else:
            return float(v)

def first(itr):
    for i in itr:
        if i is not None:
            return i
    return None

def parse(dct, key, mapping=None):
    if key not in dct:
        return None
    elif mapping is None:
        return dct[key]
    else:
        try:
            return mapping(dct[key])
        except:
            logging.debug("Error mapping field %s (value = %s)", key, dct[key])
            return None


class PhotoExif(object):
    def __init__(self, *files):
        self.files = files # possibly many files are the same photo

        self._exiftool_info = None
        self._wand_info = None

    @property
    def exiftool_info(self):
        if self._exiftool_info is None:
            self._exiftool_info = {}
            for f, file in enumerate(self.files):
                cp = subprocess.run(['exiftool', "-charset", "utf8", "-json", "-n", file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self._exiftool_info[f] = json.loads(cp.stdout.decode('utf-8'))[0]

        def inner():
            for k, v in self._exiftool_info.items():
                yield v

        return inner

    

    @property
    def width(self):
        return first(i["ImageWidth"] for i in self.exiftool_info())

    @property
    def height(self):
        return first(i["ImageHeight"] for i in self.exiftool_info())

    @property
    def date(self):
        return first(parse(i, field, lambda x: datetime.datetime.strptime(x, "%Y:%m:%d %H:%M:%S")) for i in self.exiftool_info() for field in ("DateTimeOriginal", "CreateDate"))

    @property
    def aperture(self):
        return first(parse(i, "Aperture", aperture_parse) for i in self.exiftool_info())

    @property
    def exposure(self):
        return first(parse(i, "ExposureTime", exposure_parse) for i in self.exiftool_info())

    def get_dict(self):
        return {
            'width' : self.width,
            'height' : self.height,
            'date' : self.date,
            'aperture' : self.aperture,
            'exposure' : self.exposure,
        }


    '''
    info["focal_length"] = parse(params, "FocalLength", focal_parse)
    info["focal_length_35"] = first(parse(params, "FocalLengthIn35mmFormat", focal_parse), parse(params, "FocalLength35efl", focal_parse))
    info["iso"] = parse(params, "ISO", lambda x: int(x))
    info["make"] = parse(params, "Make")
    info["model"] = parse(params, "Model")
    info["orientation"] = parse(params, "Orientation", lambda x: int(x))

    info["lens"] = parse(params, "LensModel")

    info["program"] = parse(params, "ExposureProgram", lambda x: int(x))
    info["exposure_mode"] = parse(params, "ExposureMode", lambda x: int(x))
    info["release_mode"] = parse(params, "ReleaseMode", lambda x: int(x))
    info["sequence_number"] = parse(params, "SequenceNumber", lambda x: int(x))
    '''
