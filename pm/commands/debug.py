# encoding = utf-8

from .. import models
from .. import documents

def main(*args):
    """ A convenience debugging command """
    from pprint import pprint
    import ipdb

    ps = documents.PhotoSearch()
    res = ps.execute()

    year = res.facets["date_year"]
    
    import datetime

    #date_to_str = lambda d: d.strftime("%Y-%m-%d")
    #str_to_date = lambda s: datetime.datetime.strptime(s, "%Y-%m-%d")

    #out = [(date_to_str(x[0]), x[1], x[2]) for x in date_facet]
    #inn = [(str_to_date(x[0]), x[1], x[2]) for x in out]

    import ipdb; ipdb.set_trace()
