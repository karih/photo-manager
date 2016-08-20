from flask import render_template, Response, abort
from . import app
from .models import ImageFile

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
        path = img.path
    else:
        path = getattr(img, 'path_%s' % size)

    # XXX: Return direct nginx reverse read thingy
    with open(path) as f:
        return Response(f.read(), mimetype='image/jpeg')

    I
