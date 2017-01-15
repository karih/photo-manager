import json
import datetime

from .. import app
import pm
import elasticsearch as es

class Aggregate(object):
    def __init__(self, name):
        self.name = name

    @staticmethod
    def combine_filters(filters):
        if len(filters) == 1:
            return list(filters.items())[0][1]["filter"]
        else:
            return {"bool" : {
                "must" : [f[1]["filter"] for f in filters.items() if f[1]["type"] == "must"],
                "must_not" : [f[1]["filter"] for f in filters.items() if f[1]["type"] == "must_not"]
            }}

class TermAggregate(Aggregate):
    def filter(self, value):
        return {"terms" : {self.name : [value, ]}}

    def query(self, q, filters):
        if q is None or q == "":
            filter = None
        else:
            filter = {"prefix" : {self.name : q}} 
        filters = filters.copy()
        filters.pop(self.name, None)

        req = {
            "size" : 0,
            "aggregations": {
                "agg_%s" % self.name : {
                    "terms": {"field": self.name}
                }, 
                "agg_%s_missing" % self.name : {
                    "missing": {"field": self.name}
                }
            },
            "query": self.combine_filters(filters)
        }

        self.request = req

        def consumer(query_es):
            res = query_es(req)
            buckets = [{'value' : r["key"], "count" : r["doc_count"], "selected" : r["key"] == q} for r in res["aggregations"]["agg_%s" % self.name]["buckets"]]
            valid = res["hits"]["total"] > 0
            return dict(response=res, valid=valid, buckets=buckets, null=res["aggregations"]["agg_%s_missing" % self.name]["doc_count"])
        return PhotoAggregateResult(consumer)


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

        def consumer(**kwargs):
            return dict(valid=valid, buckets=[{'value' : x} for x in candidates])
    
        return PhotoAggregateResult(consumer)


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
        self.q = q
        req = {
            "size" : 0, 
            "aggregations": {},
        }

        filters = filters.copy()
        print(filters)
        filters.pop(self.name, None)
        req["aggregations"]["agg_%s_years"  % self.name] = {
                "filter" : {"match_all" : {}},
            "aggs": {self.name : {"date_histogram" : {"field" : self.name, "interval" : "year",  "min_doc_count": 1}}}
        }

        try:
            f = self.agg_mappings[2][1](q[0:4])
            t = self.agg_mappings[2][2](f)

            filter = {"range" : {"date" : {"gte": f, "lt": t}}}
            req["aggregations"]["agg_%s_months" % self.name] = {
                "filter": filter, 
                "aggs": {self.name : {"date_histogram" : {"field" : self.name, "interval" : "month", "min_doc_count": 1}}}
            }
        except (ValueError, TypeError):
            pass

        try:
            f = self.agg_mappings[1][1](q[0:7])
            t = self.agg_mappings[1][2](f)
            
            filter = {"range" : {"date" : {"gte": f, "lt": t}}}
            req["aggregations"]["agg_%s_days"   % self.name] = {
                "filter": filter,
                "aggs": {self.name : {"date_histogram" : {"field" : self.name, "interval" : "day",   "min_doc_count": 1}}}
            }
        except (ValueError, TypeError):
            pass


        req["aggregations"]["agg_%s_missing" % self.name] = {"missing": {"field":self.name}}
        req["query"] = self.combine_filters(filters)

        self.request = req

        def consumer(query_es):
            res = query_es(req)
            years = []
            for y in res["aggregations"]["agg_%s_years" % self.name]["date"]["buckets"]:
                year_str = datetime.datetime.utcfromtimestamp(y["key"]/1000).strftime("%Y")
                year = {
                    'value' : year_str,
                    "count" : y["doc_count"], 
                    "selected" : year_str == self.q
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
                            "selected" : month_str == self.q
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
                                    "selected" : day_str == self.q
                                })
                            month["days"] = days
                        months.append(month)
                    year["months"] = months
                years.append(year)

            valid = res["hits"]["total"] > 0
            return dict(response=res, valid=valid, years=years, null=res["aggregations"]["agg_%s_missing" % self.name]["doc_count"])

        return PhotoAggregateResult(consumer)
        

class PhotoAggregateResult(dict):
    @staticmethod
    def es_query(request_body):
        return es.Elasticsearch().search(index=app.config["ELASTICSEARCH_INDEX"], body=request_body)

    def __init__(self, consumer):
        dct = consumer(query_es=self.es_query)
        dct.setdefault("response", None)
        super().__init__(**dct)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            raise AttributeError(key)
