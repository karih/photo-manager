
import json
import datetime
import logging
from flask import jsonify, Response, request, url_for
import elasticsearch as es
import elasticsearch_dsl as esd

import pm
from .. import app, db
from ..search.facets import TermFacet, PrefixFacet, DateFacet
from ..search.documents import PhotoDocument, GroupDocument
from ..search.searches import FacetedSearch
from ..models import Photo


class Aggregate(object):
    def __init__(self, name):
        self.name = name

    @classmethod
    def filter_dct(cls, filters, addons=None, exclude=None):
        filters = [value for key, value in filters.items() if (key != exclude and value is not None)]

        if addons is not None:
            if isinstance(addons, (list, tuple)):
                for add in addons:
                    if add is not None:
                        filters.append(add)
            else:
                filters.append(addons)

        if len(filters) == 0:
            filters = {"match_all": {}}
        elif len(filters) == 1:
            filters = filters[0]
        else:
            filters = {"and" : filters}

        return filters


class TermAggregate(Aggregate):
    def filter(self, value):
        return {"terms" : {self.name : [value, ]}}

    def query(self, q, filters):
        if q is None or q == "":
            filter = None
        else:
            filter = {"prefix" : {self.name : q}} 
        filter_dict = self.filter_dct(filters, filter, self.name)

        req = {
            "size" : 0, 
            "aggs": {
                "agg_%s" % self.name : {
                    "filter": filter_dict, 
                    "aggs": {self.name : {"terms" : {"field" : self.name}}}
                }, 
                "agg_%s_missing" % self.name : {
                    "filter": self.filter_dct(filters, [{"bool":{ "must_not":{"exists":{"field":self.name}}}}, ], self.name)
                }
            },
            "filter": filter_dict
        }
        
        def parse_response(res):
            valid = res["hits"]["total"] > 0
            buckets = [{'value' : r["key"], "count" : r["doc_count"], "selected" : r["key"] == q} for r in res["aggregations"]["agg_%s" % self.name][self.name]["buckets"]]
            return dict(valid=valid, buckets=buckets, null=res["aggregations"]["agg_%s_missing" % self.name]["doc_count"])

        return req, parse_response


class DirnameAggregate(Aggregate):
    def filter(self, value):
        return {"prefix" : {self.name: value}}

    def query(self, q, filters):
        # this needs to factor in the settings of other filters
        if q is not None: 
            components = q.lstrip("/").split("/")
        else:
            components = []
        tree = json.loads(pm.redis.get("cache.fstree").decode('utf-8'))
        candidates = []
        path = "/"
        valid = False
        
        for i, c in enumerate(components):
            if c in tree:
                tree = tree[c]
                path += c + "/"
            else:
                if c == "" and i+1 == len(components):
                    valid = True

                for p in tree.keys():
                    if p.startswith(c):
                        candidates.append(path + p)
                break
        else:
            valid = True
            for p in tree.keys():
                candidates.append(path + p)
        
        def parse_response(res):
            return dict(valid=valid, buckets=[{'value' : x} for x in candidates])

        return None, parse_response


class DateAggregate(Aggregate):
    agg_mappings = [
        ("day",   lambda q: datetime.datetime.strptime(q, "%Y-%m-%d"), lambda q: (q+datetime.timedelta(days=1))),
        ("month", lambda q: datetime.datetime.strptime(q, "%Y-%m"), lambda q: (q+datetime.timedelta(days=32)).replace(day=1)),
        ("year",  lambda q: datetime.datetime.strptime(q, "%Y"), lambda q: (q+datetime.timedelta(days=366)).replace(day=1)),
    ]

    def filter(self, value):
        for interval, datef, rangef in self.agg_mappings:
            try:
                f = datef(value)
                t = rangef(f)
                return {"range" : {"date" : {"gte": f, "lt": t}}}
            except (ValueError, TypeError):
                pass

        return None 

    def query(self, q, filters):
        req = {
            "size" : 0, 
            "aggs": {},
        }

        filter_dict = self.filter_dct(filters, {"match_all" : []}, self.name)
        req["aggs"]["agg_%s_years"  % self.name] = {
            "filter": filter_dict,
            "aggs": {self.name : {"date_histogram" : {"field" : self.name, "interval" : "year",  "min_doc_count": 1}}}
        }

        try:
            f = self.agg_mappings[2][1](q[0:4])
            t = self.agg_mappings[2][2](f)

            filter_dict = self.filter_dct(filters, {"range" : {"date" : {"gte": f, "lt": t}}}, self.name)
            req["aggs"]["agg_%s_months" % self.name] = {
                "filter": filter_dict, 
                "aggs": {self.name : {"date_histogram" : {"field" : self.name, "interval" : "month", "min_doc_count": 1}}}
            }
        except (ValueError, TypeError):
            pass

        try:
            f = self.agg_mappings[1][1](q[0:7])
            t = self.agg_mappings[1][2](f)
            
            filter_dict = self.filter_dct(filters, {"range" : {"date" : {"gte": f, "lt": t}}}, self.name)
            req["aggs"]["agg_%s_days"   % self.name] = {
                "filter": filter_dict,
                "aggs": {self.name : {"date_histogram" : {"field" : self.name, "interval" : "day",   "min_doc_count": 1}}}
            }
        except (ValueError, TypeError):
            pass


        req["aggs"]["agg_%s_missing" % self.name] = {"filter": self.filter_dct(filters, {"bool":{"must_not":{"exists":{"field":self.name}}}}, self.name)}
        req["filter"] = filter_dict

        def parse_response(res):
            valid = res["hits"]["total"] > 0

            years = []
            for y in res["aggregations"]["agg_%s_years" % self.name]["date"]["buckets"]:
                year_str = datetime.datetime.utcfromtimestamp(y["key"]/1000).strftime("%Y")
                year = {
                    'value' : year_str,
                    "count" : y["doc_count"], 
                    "selected" : year_str == q
                }
                
                if "agg_%s_months" % self.name in res["aggregations"]:

                    months = []
                    for m in res["aggregations"]["agg_%s_months" % self.name]["date"]["buckets"]:
                        if datetime.datetime.utcfromtimestamp(m["key"]/1000).strftime("%Y") != year_str:
                            break
                        month_str = datetime.datetime.utcfromtimestamp(m["key"]/1000).strftime("%Y-%m")
                        month = {
                            'value' : month_str,
                            "count" : m["doc_count"], 
                            "selected" : month_str == q
                        }

                        if "agg_%s_days" % self.name in res["aggregations"]:
                            days = []
                            for d in res["aggregations"]["agg_%s_days" % self.name]["date"]["buckets"]:
                                if datetime.datetime.utcfromtimestamp(d["key"]/1000).strftime("%Y-%m") != month_str:
                                    break
                                day_str = datetime.datetime.utcfromtimestamp(d["key"]/1000).strftime("%Y-%m-%d")
                                days.append({
                                    'value' : day_str,
                                    "count" : d["doc_count"], 
                                    "selected" : day_str == q
                                })
                            month["days"] = days
                        months.append(month)
                    year["months"] = months
                years.append(year)

            return dict(valid=valid, years=years, null=res["aggregations"]["agg_%s_missing" % self.name]["doc_count"])

        return req, parse_response


@app.route('/api/photos')
def photos():
    aggregate_name = request.args.get("agg")
    aggregates = [DateAggregate("date"), DirnameAggregate("dirname"), TermAggregate("model"), TermAggregate("lens")]

    filters = {}
    for a in aggregates:
        if a.name in request.args:
            if request.args[a.name] == "": # if blank, interpret like 
                filters[a.name] = {"bool":{"must_not":{"exists":{"field":a.name}}}}
            else:
                filters[a.name] = a.filter(request.args[a.name])

    # the following search stuff will be moved into its own class at some point
    if aggregate_name in [x.name for x in aggregates]:
        aggregate = [x for x in aggregates if x.name == aggregate_name][0]

        req, resf = aggregate.query(request.args.get("q"), filters)
        try:
            if req is not None:
                res = es.Elasticsearch().search(index=app.config["ELASTICSEARCH_INDEX"], body=req)
            else:
                res = None

            dct = dict(request=req, response=res)
            dct.update(resf(res))

            return jsonify(**dct)
        except es.exceptions.RequestError as e:
            return jsonify(request=req, error="Elasticsearch request error")
        except Exception as e:
            return jsonify(error=str(e))
    else:
        try:
            limit = int(request.args.get("limit"))
            if limit > 100 or limit < 1:
                limit = 20
        except (TypeError, ValueError):
            limit = 20

        try:
            offset = int(request.args.get("offset"))
            if offset > (1000 - limit) or offset < 0:
                offset = 0
        except (TypeError, ValueError):
            offset = 0


        try:
            if len(filters) == 0:
                query = {"match_all": []}
            elif len(filters) == 1:
                query = list(filters.items())[0][1]
            else:
                query = {"and" : [f[1] for f in filters.items()]}

            sort_columns = ["date", "size"]
            sort_column = "date"
            sort_order = "desc" # asc

            if "sort" in request.args and len(request.args["sort"]) > 0:
                sort_order = "desc" if (request.args["sort"][0] == "-") else "asc"

                so = request.args["sort"].lstrip("-+")
                #raise Exception(request.args["sort"], request.args["sort"].lstrip("-+"))
                if so in sort_columns:
                    sort_column = so
                
            req = {
                'query' : query,
                'from' : offset, 
                'size' : limit, 
                "sort" : {
                    sort_column : {
                        "order" : sort_order
                    }
                }
            }

            res = es.Elasticsearch().search(index=app.config["ELASTICSEARCH_INDEX"], body=req)

            def dct(photo):
                d = {}
                d["thumb_url"] = url_for('image_file', id=photo["_id"], size="thumb")
                d["id"] = photo["_id"]
                return d

            #return jsonify(query=q.to_dict(), response=r)
            return jsonify(
                request=req, 
                response=res,
                photos=[dct(photo) for photo in res["hits"]["hits"]],
                hits=res["hits"]["total"],
                offset=offset,
                limit=limit,
                sort_column=sort_column,
                sort_order=sort_order,
            )
            #photos= [dct(photo) for photo in response.hits], 
            #hits=[x.to_dict() for x in response.hits],
            #total_results=response.hits.total,
        except es.exceptions.RequestError as e:
            return jsonify(error=str(e), query=req)
        except es.exceptions.TransportError as e:
            return jsonify(error=str(e), query=req)



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
            'size' : photo.size,
            'hash' : photo.hash,
            'width' : photo.width,
            'height' : photo.height,
            'format' : photo.format,
            'date' : photo.date,
            'labels' : [(label.id, label.label) for label in photo.labels],
            'people' : [(person.id, person.name) for person in photo.people],
        }

        for file in photo.files:
            info['files'].append({
                'id' : file.id,
                'path' : file.path,
                'basename' : file.basename,
                'ctime' : file.ctime,
                'scanned' : file.scanned
            })
        return info

    p = Photo.query.get(id)
    if request.method == "PUT":
        assert "file_id" in request.get_json()
        im = [f for f in p.files if f.id == int(request.get_json().get("file_id"))][0]
        p.file_id = im.id
        db.commit()
        return jsonify(photo=get_info(p))
    else:
        return jsonify(photo=get_info(p))

'''
@app.route('/api/photos2')
def photos2():
    def date_mapping(v):
        try:
            return 'date_day', datetime.datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            try:
                return 'date_month', datetime.datetime.strptime(v, "%Y-%m")
            except ValueError as e:
                return 'date_year', datetime.datetime.strptime(v, "%Y")

    filters = {}
    mappings = {
        "aperture" : float,
        "iso" : int,
        "make" : str,
        "lens" : str,
        "focal_length_35" : float,
        "exposure" : float,
        "date" : date_mapping,
        "path" : str,
    }

    for key, val in mappings.items():
        if key in request.args:
            out = val(request.args[key])
            if isinstance(out, tuple):
                filters[out[0]] = out[1]
            else:
                filters[key] = out

    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 20))

    if limit > 20:
        limit = 20

    order = request.args.get("order", "-date")
    search = ""

    #q = Search(doc_type=[PhotoDocument, GroupDocument], index=PhotoIndex)
    q = esd.Search(doc_type=["_all", ], index="_all")
    #q = q.query('multi_match', fields=['aa', 'bb'], query=search)

    q = PhotoSearch(query=search, filters=filters).build_search()

    response = q.sort(order)[offset:offset+limit].execute()

    def dct(photo):
        d = {}
        d["thumb_url"] = url_for('image_file', id=photo.file_id, size="thumb")
        d["id"] = photo.meta.id
        return d

    facets = {}
    for key, val in PhotoSearch.facets.items():
        if key.startswith("date"):
            continue

        values = []
        for f in getattr(response.facets, key):
            values.append({'value' : f[0], 'selected' : f[2], 'count' : f[1]})
        facets[key] = values 

    years = []
    for year_value, year_count, year_selected in response.facets["date_year"]:
        months = []
        for month_value, month_count, month_selected in response.facets["date_month"]:
            if month_value.year == year_value.year:
                days = []
                for day_value, day_count, day_selected in response.facets["date_day"]:
                    if day_value.month == month_value.month and day_value.year == year_value.year:
                        days.append({'value' : day_value.strftime("%Y-%m-%d"), 'selected' : day_selected, 'count' : day_count})

                months.append({
                    'value' : month_value.strftime("%Y-%m"), 
                    'selected' : month_selected, 
                    'count' : month_count, 
                    'expanded' : any([x["selected"] for x in days]) or month_selected,
                    'days' : sorted(days, key=lambda x: x['value'])
                })
        years.append({
            'value' : year_value.strftime("%Y"), 
            'selected' : year_selected, 
            'count' : year_count, 
            'expanded' : any([x["expanded"] for x in months]) or year_selected,
            'months' : sorted(months, key=lambda x: x['value'])
        })

    facets["date_tree"] = sorted(years, key=lambda x: x['value']) 
        
    return jsonify({
        'facets' : facets,
        'photos' : [dct(photo) for photo in response.hits], 
        'results' : response.hits.total,
        'query' : q.to_dict()
    })
'''
