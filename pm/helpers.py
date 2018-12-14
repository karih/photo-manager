# encoding: utf-8

import os, sys
import os.path
import datetime
import logging

import flask

from wand.image import Image

# none of these should depend on anything below pm/

def send_file(app, f, **kwargs):
    def xaccel(p):
        r = flask.Response("")
        r.headers["X-Accel-Redirect"] = p
        r.headers["Content-Type"] = ""
        if kwargs.get("as_attachment", False):
            r.headers["Content-Disposition"] = "attachment; filename=%s" % kwargs.get("attachment_filename", os.path.basename(p))
        return r

    if not os.path.exists(f):
        raise FileNotFoundError(f)

    if app.config["USE_X_ACCEL"] and f.startswith(app.config["TEMP_DIR"]):
        return xaccel(os.path.join('/internal/tmp', f[len(app.config["TEMP_DIR"])+1:]))
    #elif app.config["USE_X_ACCEL"] and f.startswith(app.config["SEARCH_ROOT"]):
    #    return xaccel(os.path.join('/internal/root', f[len(app.config["SEARCH_ROOT"])+1:]))
    else:
        return flask.send_file(f, **kwargs)

def resize_dimensions(orig, outer):
    """ Given the original dimension `orig` and the `outer` dimension of the thumbnail,
        calculate the actual destination resolution (without cropping and stretching).
        With `box` as true, calculate the destination size and offset resulting in a 
        non-stretched cropped version of orig that fits in outer (using up all the box).
    """
    scaling = min(1, min(float(outer[0]) / orig[0], float(outer[1]) / orig[1]))
    return round(orig[0]*scaling), round(orig[1]*scaling)

def crop_box_dimensions(orig, outer):
    """ Crop the image and then scale to fit the box specified by `outer` """
   
    desired_ratio = outer[1] / outer[0]
    orig_ratio = orig[1] / orig[0]

    left, top = 0, 0
    width, height = orig
    if orig_ratio > desired_ratio:
        # image is too tall
        height = round(orig[0] * desired_ratio)
        assert orig[1] >= height
        top = round((orig[1] - height)/2)
    else:
        width = round(orig[1] / desired_ratio)
        assert orig[0] >= width
        left = round((orig[0] - width)/2)

    return {'left': left, 'top': top, 'width': width, 'height': height}

