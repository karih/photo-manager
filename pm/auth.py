from flask import g, abort, request
from . import models

__all__ = ["authenticate", "is_authenticated", "is_admin"]

def authenticate():
    if "sid" in request.cookies:
        session_id = request.cookies["sid"]
    elif "X-SESSION-ID" in request.headers:
        session_id = request.headers["X-SESSION-ID"]
    else:
        session_id = None

    if session_id is not None:
        try:
            g.session = models.Session.get_session(session_id)
            g.user = g.session.user
            return
        except ValueError as e:
            # sesssion is not valid
            pass
    g.session = None
    g.user = None

def is_authenticated(f):
    def inner(*args, **kwargs):
        if g.user is None:
            return abort(401)
        else:
            return f(*args, **kwargs)
        
    return inner

def is_admin(f):
    def inner(*args, **kwargs):
        if g.user is None:
            return abort(401)
        elif g.user.admin == False:
            return abort(403)
        else:
            return f(*args, **kwargs)
        
    return inner


