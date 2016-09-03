import datetime
from datetime import timedelta
import logging

from six import iteritems, itervalues
import elasticsearch_dsl as esd


from . import app


photos = esd.Index(app.config["ELASTICSEARCH_INDEX"])

class ExtendedDateHistogramFacet(esd.DateHistogramFacet):
	# Temporary until the elasticsearch-dsl library includes the 'year' range
    DATE_INTERVALS = {
        'year': lambda d: (d+timedelta(days=366)).replace(day=1),
        'month': lambda d: (d+timedelta(days=32)).replace(day=1),
        'week': lambda d: d+timedelta(days=7),
        'day': lambda d: d+timedelta(days=1),
        'hour': lambda d: d+timedelta(hours=1),
    }

@photos.doc_type
class PhotoDocument(esd.DocType):

    date = esd.Date()
    aperture = esd.Float()
    exposure = esd.Float()
    focal_length = esd.Float()
    focal_length_35 = esd.Float()
    iso = esd.Integer()
    make = esd.String(index='not_analyzed')
    model = esd.String(index='not_analyzed')
    lens = esd.String(index='not_analyzed')

    file_id = esd.Integer()

    def extended_dict(self):
        dct = self.to_dict()
        dct["id"] = self.meta.id
        return dct


class PhotoSearch(esd.FacetedSearch):
    doc_types = [PhotoDocument, ]

    facets = {
        'aperture' : esd.TermsFacet(field="aperture", size=10000), #, order={"_term" : "asc"}),
        'exposure' : esd.TermsFacet(field="exposure", size=10000), #, order={"_term" : "asc"}),
        'make' : esd.TermsFacet(field="make", size=10000),
        'lens' : esd.TermsFacet(field="lens", size=10000),
        'iso' : esd.TermsFacet(field="iso", size=10000),
        'focal_length_35' : esd.HistogramFacet(field="focal_length_35", interval=10, min_doc_count=1),
        'date_day'   : ExtendedDateHistogramFacet(field='date', min_doc_count=1, interval='day'),
        'date_month' : ExtendedDateHistogramFacet(field='date', min_doc_count=1, interval='month'),
        'date_year'  : ExtendedDateHistogramFacet(field='date', min_doc_count=1, interval='year')
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
