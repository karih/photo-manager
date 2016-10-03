import json
import logging
import os.path

from flask import jsonify, url_for, request
import pm 
from ..models import File, Photo, Group

def image_dict(image):
    dct = image.dct()
    dct["original_url"] = url_for('image_file', id=image.id, size="original")
    dct["thumb_url"] = url_for('image_file', id=image.id, size="thumb")
    dct["large_url"] = url_for('image_file', id=image.id, size="large")
    return dct

@pm.app.route('/api/files')
def files():
    """ Returns ImageFile objects after filtering, offsetting and limiting """
    # TODO: Move to elasticsearch

    prefix = request.args.get("filter", None)
    offset = int(request.args.get("offset", 0))
    try:
        limit  = int(request.args.get("limit", 20))
        if limit > 20:
            limit = 20
    except ValueError as e:
        limit = 20

    order = request.args.get("order", None)

    def dct(image):
        d = {}
        d["thumb_url"] = url_for('image_file', id=image.id, size="thumb")
        d["filename"] = image.basename
        d["id"] = image.id
        d["date"] = image.photo.date
        return d


    query = File.query.filter(File.deleted == False).filter(File.photo != None)
    if prefix is not None:
        query = query.filter(File.path.like('%s%%' % prefix))

    query = query.order_by(File.path)
    query = query.offset(offset).limit(limit)

    return jsonify(images=[dct(i) for i in query])

@pm.app.route('/api/file/<int:id>', methods=['GET'])
def file(id):
    """ Returns information dict() about ImageFile """

    image = Photo.query.get(id)
    return jsonify(image=image_dict(image))


@pm.app.route('/api/filesystem', methods=['GET'])
def filesystem():
    """ 
        A very poor way of creating a json object describing the 
        filesystem tree displayed in the file manager.
        
        Should at least be cached or something.., querying all 
        imagefile objects is not a good idea.
    """

    if not pm.redis.exists("cache.fstree"):
        logging.info("Building fstree")
        root = {}

        def unfold(p):
            segments = p.split("/")[1:] # exclude filename
            current = root
            while len(segments) > 0:
                if segments[0] not in current:
                    current[segments[0]] = {}

                current = current[segments.pop(0)]

        files = File.query.filter(File.deleted==False).filter(File.photo != None).all()
        paths = [os.path.split(f.path)[0] for f in files]

        for path in paths:
            unfold(path)
        
        pm.redis.set('cache.fstree', json.dumps(root).encode('utf-8')) 
    else:
        logging.info("Loading fstree from cache")
        root = json.loads(pm.redis.get("cache.fstree").decode('utf-8'))

    return jsonify(filesystem=root)
