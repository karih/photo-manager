import os
import json
import logging

from ..models import File
import pm

def main():
    def filesystem():
        """ 
            This can most likely be made considerably more efficient..
        """

        logging.debug("Building fstree")
        root = {}

        def unfold(p):
            segments = p.split("/")[1:] # exclude filename
            current = root
            while len(segments) > 0:
                if segments[0] not in current:
                    current[segments[0]] = {}

                current = current[segments.pop(0)]

        files = File.query.filter(File.deleted==False).filter(File.photo != None).all()
        paths = [os.path.split(f.path)[0] for f in files]

        for path in paths:
            unfold(path)
        
        pm.redis.set('cache.fstree', json.dumps(root).encode('utf-8')) 

    filesystem()
