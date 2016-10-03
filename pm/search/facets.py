import elasticsearch as es
import elasticsearch_dsl as esd

class Facet(object):
    def __init__(self, name):
        self.name = name

    def is_filtered(self, filters):
        return self.name in filters is not None

    def aggregates(self):
        return [
            (self.name, esd.A(self.agg_type, field=self.name, size=5)), 
            ("%s_missing" % self.name, esd.A("missing", field=self.name)) 
        ]

    def consume(self, filters, **kwargs):
        return {
            "buckets" : [{"key" : x.key, "doc_count" : x.doc_count, "active" : x.key == filters.get(self.name)} for x in kwargs[self.name][self.name]["buckets"]],
            "outside_buckets" : kwargs[self.name][self.name]["sum_other_doc_count"],
            "total_docs" : kwargs[self.name]["doc_count"]
        }


class TermFacet(Facet):
    agg_type = "terms"

    def filters(self, args):
        if self.name in args and args[self.name] == "":
            return esd.Q('missing', field=self.name)
        else:
            return esd.Q('terms', **{self.name : [args.get(self.name), ]})


class PrefixFacet(TermFacet):
    def filters(self, args):
        if self.name in args and len(self.name) > 0:
            return esd.Q('prefix', **{self.name : args.get(self.name), })
        else:
            return super().filters(args)


class DirectoryTreeFacet(PrefixFacet):
    pass


#class RangeFacet(Facet):
#    agg_type = "range"
#
#    def extract_params(self, args):
#        if self.name in args:
#            self.value = float(args[self.name])
#        else:
#            self.value = [None, None]
#            if "%s_lt" % self.name in args:
#                self.value[1] = float(args["%s_lt" % self.name])
#            if "%s_gt" % self.name in args:
#                self.value[0] = float(args["%s_gt" % self.name])
#
#    def filters(self, filters):
#        if self.name in filters:
#            return esd.Q('terms', **{self.name : [filters.get(self.name), ]})
#        else:
#            range = {}
#            if "%s_from" % self.name in filters:
#                range["from"] = filters.get("%s_from" % self.name)
#            if "%s_to" % self.name in filters:
#                range["to"] = filters.get("%s_to" % self.name)
#            if len(range.keys()) > 0:
#                return esd.Q('range', **{self.name : range})
#
#    def is_filtered(self, filters):
#        return self.name in filters or "%s_from" % self.name in filters  or "%s_to" % self.name in filters
#
#    def aggregates(self):
#        return [(self.name, esd.A(self.agg_type, **{'field' : self.name, 'ranges' : [], 'keyed' : False})), ]
#
#
#
class HistogramFacet(Facet):
    agg_type = "histogram"

    def __init__(self, *args, **kwargs):
        self.interval = kwargs.get("interval")
        super().__init__(*args, **kwargs)

    def filters(self):
        range = {}
        if self.value[0] is not None:
            range["from"] = self.value[0]
        if self.value[1] is not None:
            range["to"] = self.value[1]
        return esd.Q('range', **{self.name : range})

    def aggregates(self):
        return [(self.name, esd.A(self.agg_type, **{'field' : self.name, 'interval' : self.interval})), ]


class DateFacet(HistogramFacet):
    agg_type = 'date_histogram'

    aggregations = (
        ('date_year', 'year', '%Y', lambda x: (x + datetime.timedelta(days=366)).replace(day=1)),
        ('date_month', 'month', '%Y-%m', lambda x: (x + datetime.timedelta(days=32)).replace(day=1)),
        ('date_day', 'day', '%Y-%m-%d', lambda x: x + datetime.timedelta(days=1)),
    )

    def aggregates(self):
        aggs = []
        for name, interval, format, f in self.aggregations:
            aggs.append((name, esd.A(self.agg_type, **{'field' : self.name, 'interval' : interval, 'min_doc_count' : 1})))
        return aggs

    def extract_params(self, args):
        self.value = None
        if self.name in args:
            for key, interval, format, deltaf in self.aggregations:
                try:
                    value = datetime.datetime.strptime(args[self.name], format)
                    self.value = value, deltaf(value) 
                    self.key = key
                    break
                except ValueError as e:
                    pass
            else:
                raise ValueError("Invalid date format")
