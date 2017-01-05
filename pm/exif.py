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
            logging.error("Error mapping field %s (value = %s)", key, dct[key])
            return None

def wand_extract_info(orig_filename):
    raise NotImplementedException()
    # leaving this for now, but can probably be safely removed

    info = INFO.copy()
    
    with Image(filename=orig_filename) as im:
        logging.debug("Opened file %s", orig_filename)
        m = im.metadata
        info["width"] = im.width
        info["height"] = im.height
        if im.width < 1 or im.height < 1:
            raise ValueError("Could not read image object (non-positive dimensions)")

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

        logging.debug("Closing file %s", orig_filename)

    return info


def exiftool_extract_info(orig_filename):
    cp = subprocess.run(['exiftool', "-charset", "utf8", "-json", "-n", orig_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    params = json.loads(cp.stdout.decode('utf-8'))[0]
    info = INFO.copy()

    info["width"] = params["ImageWidth"]
    info["height"] = params["ImageHeight"]
    info["date"] = first(
        parse(params, "DateTimeOriginal", lambda x: datetime.datetime.strptime(x, "%Y:%m:%d %H:%M:%S")),
        parse(params, "CreateDate", lambda x: datetime.datetime.strptime(x, "%Y:%m:%d %H:%M:%S")),
    )

    info["aperture"] = parse(params, "Aperture", aperture_parse)
    info["exposure"] = parse(params, "ExposureTime", exposure_parse)
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

    return info
