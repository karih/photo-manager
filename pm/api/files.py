import os.path

from flask import jsonify, url_for, request
from .. import app
from ..models import ImageFile

def image_dict(image):
    dct = image.dct()
    dct["original_url"] = url_for('image_file', id=image.id, size="original")
    dct["thumb_url"] = url_for('image_file', id=image.id, size="thumb")
    dct["large_url"] = url_for('image_file', id=image.id, size="large")
    return dct

@app.route('/api/files')
def files():
    """ Returns ImageFile objects after filtering, offsetting and limiting """

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
        d["filename"] = os.path.split(image.full_path)[1]
        d["id"] = image.id
        d["date"] = image.date
        return d


    query = ImageFile.query
    if prefix is not None:
        query = query.filter(ImageFile.path.like('%s%%' % prefix))

    query = query.order_by(ImageFile.path)
    query = query.offset(offset).limit(limit)

    return jsonify(images=[dct(i) for i in query])

@app.route('/api/file/<int:id>', methods=['GET'])
def file(id):
    """ Returns information dict() about ImageFile """

    image = ImageFile.query.get(id)
    return jsonify(image=image_dict(image))


@app.route('/api/filesystem', methods=['GET'])
def filesystem():
    """ 
        A very poor way of creating a json object describing the 
        filesystem tree displayed in the file manager.
        
        Should at least be cached or something.., querying all 
        imagefile objects is not a good idea.
    """
    root = {}

    def unfold(p):
        segments = p.split("/")[1:] # exclude filename
        current = root
        while len(segments) > 0:
            if segments[0] not in current:
                current[segments[0]] = {}

            current = current[segments.pop(0)]

    files = ImageFile.query.all()
    paths = [os.path.split(f.path)[0] for f in files]

    for path in paths:
        unfold(path)

    return jsonify(filesystem=root)

