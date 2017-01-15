import elasticsearch as es

from .. import app
from .aggregates import Aggregate, TermAggregate, DirnameAggregate, DateAggregate

class PhotoResult(object):
    def __init__(self, search, response):
        self.search = search
        self.response = response
        self.parse()

    def parse(self):
        offset, limit = self.search.offset, self.search.limit
        hits = self.response["hits"]["hits"]
        self.previous_id = hits[0]["_id"] if (offset > 0 and len(hits) > 0) else None
        self.next_id = hits[-1]["_id"] if (len(hits) == ((limit + 2) if offset > 0 else (limit + 1)) and ((len(hits) == (limit + 2) and offset > 0) or ((len(hits) == (limit + 1)) and offset == 0))) else None
        self.hits = self.response["hits"]["total"]
        self.documents = hits[1:limit+1] if offset > 0 else hits[0:limit]


class PhotoSearch(object):
    def __init__(self, args):
        self.aggregates = [
            DateAggregate("date"), 
            DirnameAggregate("dirname"), 
            TermAggregate("model"), 
            TermAggregate("lens")
        ]
        self.args = args

    @property
    def is_aggregate_query(self):
        return "agg" in self.args

    def execute(self): 
        filters = {}
        for a in self.aggregates:
            if a.name in self.args:
                if self.args[a.name] == "": # if blank, interpret like 
                    filters[a.name] = {"type": "must_not", "filter" : {"exists" : {"field" : a.name}}}
                else:
                    filters[a.name] = {"type": "must", "filter" : a.filter(self.args[a.name])}

        if self.is_aggregate_query:
            aggregate_query = self.args.get("q")
            aggregate = [x for x in self.aggregates if x.name == self.args.get("agg")][0]

            result = aggregate.query(self.args.get("q"), filters)
            self.request = aggregate.request if hasattr(aggregate, "request") else None
        else:
            try:
                limit = int(self.args.get("limit"))
                if limit > 100 or limit < 1:
                    limit = 20
            except (TypeError, ValueError):
                limit = 20

            try:
                offset = int(self.args.get("offset"))
                if offset > (10000 - limit) or offset < 0:
                    offset = 0
            except (TypeError, ValueError):
                offset = 0

            self.offset = offset
            self.limit = limit
            req = {}
            req["query"] = Aggregate.combine_filters(filters)

            sort_columns = ["date", "size"]
            self.sort_column = "date"
            self.sort_order = "desc" # asc

            if "sort" in self.args and len(self.args["sort"]) > 0:
                self.sort_order = "desc" if (self.args["sort"][0] == "-") else "asc"

                so = self.args["sort"].lstrip("-+")
                if so in sort_columns:
                    self.sort_column = so
            
            req["from"] = (offset - 1) if offset > 0 else offset
            req["size"] = (limit + 2) if offset > 0 else (limit + 1)
            req["sort"] = { self.sort_column : { "order" : self.sort_order } }

            self.request = req

            result = PhotoResult(self, es.Elasticsearch().search(index=app.config["ELASTICSEARCH_INDEX"], body=req))

        return result

