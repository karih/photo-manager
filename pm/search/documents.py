import datetime
from datetime import timedelta
import logging

from six import iteritems, itervalues
import elasticsearch_dsl as esd


from .. import app


PhotoIndex = esd.Index(app.config["ELASTICSEARCH_INDEX"])
# So this allows bigger pagination in /photos, probably going past 10000/20 pages doesn't 
# make a whole lot of sense, and this should be solved differently, but until that time..
PhotoIndex.settings(max_result_window=500000) 

class ExtendedDateHistogramFacet(esd.DateHistogramFacet):
	# Temporary until the elasticsearch-dsl library includes the 'year' range
    DATE_INTERVALS = {
        'year': lambda d: (d+timedelta(days=366)).replace(day=1),
        'month': lambda d: (d+timedelta(days=32)).replace(day=1),
        'week': lambda d: d+timedelta(days=7),
        'day': lambda d: d+timedelta(days=1),
        'hour': lambda d: d+timedelta(hours=1),
    }

@PhotoIndex.doc_type
class PhotoDocument(esd.DocType):
    date = esd.Date()
    aperture = esd.Float()
    exposure = esd.Float()
    focal_length = esd.Float()
    focal_length_35 = esd.Float()
    iso = esd.Integer()
    size = esd.Integer()
    model = esd.String(index='not_analyzed') #analyzer=esd.analyzer('keyword', tokenizer="keyword", filter=['lowercase', ]))
    model_ci = esd.String(analyzer=esd.analyzer('keyword', tokenizer="keyword", filter=['lowercase', ]))
    lens = esd.String(index='not_analyzed')
    lens_ci = esd.String(analyzer=esd.analyzer('keyword', tokenizer="keyword", filter=['lowercase', ]))
    path = esd.String(index='not_analyzed')
    dirname = esd.String(index='not_analyzed')
    basename = esd.String(index='not_analyzed')

    def extended_dict(self):
        dct = self.to_dict()
        dct["id"] = self.meta.id
        return dct

@PhotoIndex.doc_type
class GroupDocument(esd.DocType):
    date = esd.Date()
    aperture = esd.Float()
    exposure = esd.Float()
    focal_length = esd.Float()
    focal_length_35 = esd.Float()
    iso = esd.Integer()
    model = esd.String(index='not_analyzed') #analyzer=esd.analyzer('keyword', tokenizer="keyword", filter=['lowercase', ]))
    lens = esd.String(index='not_analyzed')
    path = esd.String(index='not_analyzed')
    dirname = esd.String(index='not_analyzed')
    basename = esd.String(index='not_analyzed')


class PhotoSearch(esd.FacetedSearch):
    doc_types = [PhotoDocument, ]

    facets = {
        'aperture' : esd.TermsFacet(field="aperture"), #, order={"_term" : "asc"}),
        'exposure' : esd.TermsFacet(field="exposure"), #, order={"_term" : "asc"}),
        'model' : esd.TermsFacet(field="model"),
        'lens' : esd.TermsFacet(field="lens"),
        'iso' : esd.TermsFacet(field="iso"),
        'focal_length_35' : esd.HistogramFacet(field="focal_length_35", interval=10),
        'dirname' : esd.TermsFacet(field="dirname"),
        'date_day'   : ExtendedDateHistogramFacet(field='date', interval='day'),
        'date_month' : ExtendedDateHistogramFacet(field='date', interval='month'),
        'date_year'  : ExtendedDateHistogramFacet(field='date', interval='year')
    }

    def aggregate(self, search):
        """
        Add aggregations representing the facets selected, including potential
        filters.
        """
        for f, facet in iteritems(self.facets):
            agg = facet.get_aggregation()
            agg_filter = esd.Q('match_all')
            for field, filter in iteritems(self._filters):
                if f == field or (f.startswith("date") and field.startswith("date")):
                    continue
                agg_filter &= filter
            search.aggs.bucket(
                '_filter_' + f,
                'filter',
                filter=agg_filter
            ).bucket(f, agg)
