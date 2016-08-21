# encoding: utf-8

import os, sys
import datetime
import logging
import numpy as np

import flask

from PIL import Image as PILImage
from PIL import ExifTags
from wand.image import Image

from . import app


def process(orig_filename, thumbnails):
    def first(*lst):
        for i in lst:
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
                logging.error("Error mapping field %s (%s, %s)", dct[key], dct, key)
                return None

    def aperture_parse(v):
        if v[0:2].lower() == "f/":
            return float(v[2:])
        elif v[0].lower() == "f":
            return float(v[1:])
        elif "/" in v:
            x, y = v.split("/")
            return float(x)/int(y)

    def exposure_parse(v):
        if " " in v:
            v = v.split(" ")[0]

        if "/" in v:
            x, y = v.split("/")
            return float(x) / int(y)
        else:
            return float(v)

    def focal_parse(v):
        if " " in v:
            v = v.split(" ")[0]

        if "/" in v:
            x, y = v.split("/")
            return float(x) / int(y)
        else:
            return float(v)

        
    info = {}
    
    with Image(filename=orig_filename) as im:
        stat = os.stat(orig_filename)
        m = im.metadata
        info["width"] = im.width
        info["height"] = im.height
        info["ctime"] = datetime.datetime.fromtimestamp(stat.st_ctime)
        info["date"] = parse(m, "exif:DateTime", lambda x: datetime.datetime.strptime(x, "%Y:%m:%d %H:%M:%S"))
        info["aperture"] = first(
                parse(m, "dng:Aperture", aperture_parse),
                parse(m, "exif:FNumber", aperture_parse),
        )
        info["exposure"] = first(
                parse(m, "dng:Shutter", exposure_parse),
                parse(m, "exif:ExposureTime", exposure_parse)
        )
        info["focal_length"] = first(
                parse(m, "dng:FocalLength", focal_parse),
                parse(m, "exif:FocalLength", focal_parse)
        ) 
        info["focal_length_35"] = first(
                parse(m, "dng:FocalLength35", lambda x: float(x[0:-3])),
                parse(m, "exif:FocalLengthIn35mmFilm", lambda x: float(x))
        ) 
        info["iso"] = first(parse(m, "dng:ISOSpeed", lambda x: int(x)), parse(m, "exif:ISOSpeedRatings", lambda x: int(x)))
        info["make"] = first(parse(m, "dng:Make"), parse(m, "exif:Make"))
        info["model"] = first(parse(m, "dng:Model"), parse(m, "exif:Model"))
        info["orientation"] = first(parse(m, "exif:Orientation", lambda x: int(x)))

        info["lens"] = first(parse(m, "dng:Lens"))

        logging.debug([x for x in m.items() if "focal" in x[0].lower()])
        logging.debug([x for x in m.items() if "lens" in x[0].lower()])

        for size, dest in thumbnails:
            with im.clone() as cl:
                cl.format = 'jpeg'
                cl.auto_orient()
                cl.resize(*resize_dimensions((cl.width, cl.height), size))
                cl.save(filename=dest)
        logging.debug("Closing file %s" % orig_filename)

    return info

def resize_dimensions(orig, outer):
    scaling = min(1, min(float(outer[0]) / orig[0], float(outer[1]) / orig[1]))
    return np.round(orig[0]*scaling).astype(int), np.round(orig[1]*scaling).astype(int)

def send_file(f):
    def xaccel(p):
        r = flask.Response("")
        r.headers["X-Accel-Redirect"] = p
        r.headers["Content-Type"] = ""
        return r

    if app.config["USE_X_ACCEL"] and f.startswith(app.config["TEMP_DIR"]):
        return xaccel(os.path.join('/internal/tmp', f[len(app.config["TEMP_DIR"])+1:]))
    elif app.config["USE_X_ACCEL"] and f.startswith(app.config["SEARCH_ROOT"]):
        return xaccel(os.path.join('/internal/root', f[len(app.config["SEARCH_ROOT"])+1:]))
    else:
        return flask.send_file(f)

