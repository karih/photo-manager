from functools import partial

import elasticsearch as es
import elasticsearch_dsl as esd

class FacetedResponse(esd.result.Response):
    def __init__(self, *args, **kwargs):
        search = kwargs.pop("search")
        super(FacetedResponse, self).__init__(*args, **kwargs)
        super(esd.utils.AttrDict, self).__setattr__('_search', search)

    @property
    def facets(self):
        if not hasattr(self, "_facets"):
            super(esd.utils.AttrDict, self).__setattr__('_facets', esd.utils.AttrDict({}))
            for facet in self._search.facets:
                if "include_%s" % facet.name in self._search.args:
                    self._facets[facet.name] = facet.consume(self._search.args, **{akey: self.aggregations["_filter_" + akey] for akey, adct in facet.aggregates()})

        return self._facets

#    @property
#    def query_string(self):
#        return self._search._query
#
#    @property
#    def facets(self):
#        if not hasattr(self, '_facets'):
#            super(AttrDict, self).__setattr__('_facets', AttrDict({}))
#            for name, facet in iteritems(self._search.facets):
#                self._facets[name] = facet.get_values(
#                    self.aggregations['_filter_' + name][name]['buckets'],
#                    self._search.filter_values.get(name, ())
#                )
#        return self._facets


class FacetedSearch(esd.Search):
    def __init__(self, *args, **kwargs):
        self.facets = kwargs.pop("facets", None)
        self.args = kwargs.pop("args", None)
        super().__init__(*args, **kwargs)
        self._response_class = partial(FacetedResponse, search=self)

    def build(self):
        fs = self._clone()

        for facet in self.facets:
            if "include_%s" % facet.name not in self.args:
                continue

            agg_filter = esd.Q("match_all")
            for inner in self.facets:
                if inner.name != facet.name:
                    if inner.is_filtered(self.args):
                        agg_filter &= inner.filters(self.args)

            for agg_name, agg in facet.aggregates():
                fs.aggs.bucket("_filter_" + agg_name, "filter", filter=agg_filter).bucket(agg_name, agg)

        post_filter = esd.Q('match_all')
        for facet in self.facets:
            if facet.is_filtered(self.args):
                post_filter &= facet.filters(self.args)
        fs.post_filter._proxied &= post_filter

        return fs

    def _clone(self):
        fs = super()._clone()
        fs.facets = self.facets
        fs.args = self.args.copy()
        fs._response_class = partial(FacetedResponse, search=self)
        return fs
