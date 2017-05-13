import os.path

from flask import make_response, redirect, render_template, Response, abort, request, g
from . import app
from .models import User, File, Session
from .helpers import send_file



@app.route('/login', methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    try:
        user = User.authenticate(username, password)
        session = Session.create_session(user)
        response = make_response("logged in")
        response.set_cookie("sid", session.key, 
            secure  =app.config["SESSION_COOKIE_SECURE"],
            path    =app.config["SESSION_COOKIE_PATH"],
            httponly=app.config["SESSION_COOKIE_HTTPONLY"]
        )
        return response
    except ValueError as e:
        return redirect('/', code=302) 

@app.route('/logout', methods=["POST"])
def logout():
    g.session.destroy()
    return redirect('/', code=302) 


@app.route('/image/<id>/<size>')
def image_file(id, size):
    """ The actual jpg image drop-off view """
    img = Photo.query.get(id)
    if img is None or img.deleted:
        abort(404)

    if size not in ('original', 'large', 'thumb'):
        abort(403)

    # XXX: Careful..
    if size == "original": 
        return send_file(app, img.files[0].path, as_attachment=True, attachment_filename=img.basename)
    else:
        return send_file(app, getattr(img, 'path_%s' % size))

@app.route('/s/<album_set>')
def view_album_set(album_set):
    # view a set of albums
    pass

@app.route('/a/<album_shortname>/download')
def album_download(album_shortname):
    # direct download of an album as tar.gz/zip
    # option: format - specific format
    # option: highres - include originals where allowed
    pass

@app.route('/a/<album_shortname>')
def view_album(album_shortname):
    # view an album
    pass

@app.route('/i/<share_key>')
def view_image(share_key):
    # direct link to an image (displayed inside some html)
    pass



@app.route('/')
def index():
    """ The index site """
    return render_template('index.html', logged_in=g.user is not None, username=g.user.username if g.user else None)

@app.route('/l')
@app.route('/l/<path:path>')
def library(path=None):
    """ The library site """
    return render_template('library.html')
