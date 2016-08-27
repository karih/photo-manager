import os.path

from flask import render_template, Response, abort, request
from . import app
from .models import ImageFile
from .helpers import send_file


@app.route('/')
@app.route('/<path:path>')
def index(path=None):
    return render_template('index.html')


@app.route('/image/<id>/<size>')
def image_file(id, size):
    img = ImageFile.query.get(id)
    if size not in ('original', 'large', 'thumb'):
        abort(403)

    # XXX: Careful..
    if size == "original": 
        return send_file(img.path, as_attachment=True, attachment_filename=os.path.basename(img.path))
    else:
        return send_file(getattr(img, 'path_%s' % size))
