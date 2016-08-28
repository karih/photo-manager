import elasticsearch_dsl as esd


photos = esd.Index('photos')


@photos.doc_type
class PhotoDocument(esd.DocType):

    date = esd.Date()
    aperture = esd.Float()
    focal_length_35 = esd.Integer()
    iso = esd.Integer()

    def extended_dict(self):
        dct = self.to_dict()
        dct["id"] = self.meta.id
        return dct


class PhotoSearch(esd.FacetedSearch):
    doc_types = [PhotoDocument, ]

    facets = {
        'aperture' : esd.TermsFacet(field="aperture", size=10000),
        'iso' : esd.TermsFacet(field="iso", size=10000),
        'focal_length_35' : esd.HistogramFacet(field="focal_length_35", interval=10, min_doc_count=1),
        'date' : esd.DateHistogramFacet(field='date', interval='day', min_doc_count=1)
    }


