# encoding = utf-8

from .. import models
from .. import documents

def main(*args):
    """ A convenience debugging command """

    ps = documents.PhotoSearch()
    import ipdb; ipdb.set_trace()
