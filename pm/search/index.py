import elasticsearch as es

from .. import app, es
from .. import models

class Index(object):
    settings = {
        "analysis": {
            "analyzer": {
                "keyword": {
                    "type": "custom", 
                    "tokenizer": "keyword", 
                    "filter": ["lowercase"]
                }
            }
        }, 
        "max_result_window": 500000
    }

    def create(self):
        es.indices.create(
            index=app.config["ELASTICSEARCH_INDEX"],
            body={"mappings": {k: v for k, v in self.get_mappings()}, "settings" : self.settings}
        )
    
    def delete(self):
        es.indices.delete(index=app.config["ELASTICSEARCH_INDEX"], ignore=[400, 404])
    
    def get_mappings(self):
        for obj in dir(models):
            if hasattr(getattr(models, obj), "__document_name__"):
                yield getattr(models, obj).__document_name__, getattr(models, obj).__document__
