
import datetime
import logging
from flask import jsonify, Response, request, url_for

from .. import app
from ..documents import PhotoDocument, PhotoSearch
from ..models import Photo

@app.route('/api/photos')
def photos():
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
        "date" : date_mapping
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

