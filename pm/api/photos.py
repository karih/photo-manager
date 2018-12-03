
import json
import datetime
import logging

import flask
from flask import jsonify, Response, request, url_for, abort
import elasticsearch as es

import pm
from .. import app, db, models
from ..search.searches import PhotoSearch
from ..models import Photo


logger = logging.getLogger(__name__)


@app.route('/api/photos')
def photos():
    search = PhotoSearch(request.args)
                
    def dct(photo):
        d = {}
        d["thumb_url"] = url_for('image_file', id=photo["_id"], size="thumb")
        d["id"] = photo["_id"]
        return d

    try:
        out = {}
        result = search.execute()
        out["request"] = search.request
        out["response"] = result.response
        
        if search.is_aggregate_query:
            # future api
            out.update(result)
        else:
            out["hits"] = result.hits
            out["offset"] = search.offset
            out["limit"] = search.limit
            out["previous"] = result.previous_id
            out["next"] = result.next_id
            out["sort_column"] = search.sort_column
            out["sort_order"] = search.sort_order
            out["photos"] = [dct(doc) for doc in result.documents]

        return jsonify(out)
    except es.exceptions.RequestError as e:
        raise
        return jsonify(request=req, error="Elasticsearch request error", details=str(e))
    except es.exceptions.TransportError as e:
        raise
        return jsonify(request=req, error="Elasticsearch transport error", details=str(e))
    except Exception as e:
        raise
        return jsonify(error=str(e))

@app.route('/api/photo/<int:id>', methods=["GET", "PUT"])
def photo(id):
    def get_info(photo):
        info = {
            'id' : photo.id,
            'thumb_url' : url_for('image_file', id=photo.id, size="thumb"),
            'large_url' : url_for('image_file', id=photo.id, size="large"),
            'date' : photo.date,
            'aperture' : photo.aperture,
            'exposure' : photo.exposure,
            'focal_length' : photo.focal_length,
            'focal_length_35' : photo.focal_length_35,
            'iso' : photo.iso,
            'make' : photo.make,
            'model' : photo.model,
            'lens' : photo.lens,
            'changed' : photo.changed,
            'files' : [],
            'width' : photo.width,
            'height' : photo.height,
            'date' : photo.date,
            'labels' : [{"id": label.id, "label": label.label} for label in photo.labels],
        }

        for i, file in enumerate(photo.files):
            if i == 0:
                info['sizes'] = {size: flask.url_for('image_file', id=file.id, size=size) for size in app.config["SIZES"].keys()}

            info['files'].append({
                'id' : file.id,
                'path' : file.path,
                'basename' : file.basename,
                'ctime' : file.ctime,
                'hash' : file.hash,
                'size' : file.size,
                'scanned' : file.scanned,
                'sizes' : {size: flask.url_for('image_file', id=file.id, size=size) for size in app.config["SIZES"].keys()}
            })
        return info

    p = Photo.query.get(id)

    if p is None or p.deleted:
        abort(404)

    if request.method == "PUT":
        labels = request.get_json().get("labels", None)
        if labels is not None:
            p.labels = [models.Label.query.get(id) for id in labels]
        db.commit()
        return jsonify(photo=get_info(p))
    else:
        return jsonify(photo=get_info(p))


class Query(object):
    def __init__(self, aggregates, args):
        self.aggregates = aggregates
        self.args = args

    @property
    def is_aggregate_query(self):
        return "agg" in self.args

    def query_filter(self):
        must = []
        must_not = []

        for a in self.aggregates:
            if a.name in request.args and not (self.is_aggregate_query and request.args["agg"] == a.name):
                if request.args[a.name] == "":
                    must_not.append({"exists" : {"field" : a.name}})
                else:
                    must.append(a.filter(request.args[a.name]))

        out = {"bool" : {}}
        if len(must) > 0:
            out["bool"]["must"] = must
        if len(must_not) > 0:
            out["bool"]["must_not"] = must_not
        return out
    
    def construct_query(self):
        pass
