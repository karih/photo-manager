import os.path

import flask
from flask import make_response, redirect, render_template, Response, abort, request, g
from . import app, es
from .models import User, File, Session, Photo
from .helpers import send_file


@app.route('/login', methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    redirect_uri = request.args.get("redirect", request.headers.get("referer", None))

    try:
        user = User.authenticate(username, password)
        session = Session.create_session(user)
        response = make_response("logged in -- no redirect url or referer header" if redirect_uri is None else redirect(redirect_uri))
        response.set_cookie("sid", session.key, 
            secure  =app.config["SESSION_COOKIE_SECURE"],
            path    =app.config["SESSION_COOKIE_PATH"],
            httponly=app.config["SESSION_COOKIE_HTTPONLY"]
        )
        return response

    except ValueError as e:
        return render_template('login.html', error="Invalid username/password")


@app.route('/logout', methods=["GET", "POST"])
def logout():
    g.session.destroy()
    return redirect('/', code=302) 


@app.route('/file/<id>/<size>')
def image_file(id, size):
    """ The actual jpg image drop-off view """
    if size not in app.config["SIZES"].keys():
        abort(403)

    file = File.query.get(id)
    if file is None or file.deleted:
        abort(404)

    # XXX: Careful..
    try:
        if app.config["SIZES"][size][0] is None: # original file 
            #return send_file(app, file.path, as_attachment=True, attachment_filename=file.basename)
            return send_file(app, file.path)
        else:
            return send_file(app, file.get_path(size))
    except FileNotFoundError:
        abort(503) # Service Unavailable




@app.route('/simple_search')
def simple_search():
    query = es.search(
        index=app.config["ELASTICSEARCH_INDEX"], 
        q=request.args["q"],
        from_=request.args.get("offset", 0),
        size=request.args.get("limit", 20)
    )

    def map_result_to_answer(dct):
        _dct = dct["_source"]
        _dct['files'] = {size: flask.url_for('image_file', id=_dct['file_id'], size=size) for size in app.config["SIZES"].keys()}
        return _dct

    results = [map_result_to_answer(x) for x in query["hits"]["hits"]]
    return flask.jsonify(photos=results, total= query["hits"]["total"])


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

@app.route('/l')
@app.route('/l/')
@app.route('/l/<path:path>')
def library(path=None):
    """ The library site """
    if g.user is None:
        return render_template('login.html')
    else:
        return render_template('library.html')

@app.route('/')
def index():
    """ The index site """
    return render_template('index.html', logged_in=g.user is not None, username=g.user.username if g.user else None)
