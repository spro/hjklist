import json
import time
from collections import defaultdict
import pymongo
import bson.json_util
from bson.objectid import ObjectId as oid

class attrdict(defaultdict):
    def __getattr__(self, key): return self[key]
    def __setattr__(self, key, val): self[key]=val

def tree(): return attrdict(tree)

def pymongo_to_json(thing):
    return json.dumps(thing, default=bson.json_util.default)

class Document(dict):
    types = {}
    def __getattr__(self, key):
        if self.has_key(key): return self[key]
        else: return None
    #def __setattr__(self, key, val): self[key]=val
    @property
    def id(self):
        return self._id
    @property
    def id_str(self):
        return str(self.id) if self.id else ''
    def to_json(self): return pymongo_to_json(self)

class Collection(object):
    type = Document
    def fetch(self, **query):
        return [self.type(item) for item in self.collection.find(query)]
    def get(self, **query):
        if query.has_key('_id'):
            query['_id'] = oid(query['_id'])
        found = self.collection.find_one(query)
        if found:
            return self.type(found)
        else:
            return None
    def count(self, **query):
        return self.collection.find(query).count()
    def exists(self, **query):
        return self.count(**query) > 0
    def new(self, **data):
        _id = self.collection.insert(data)
        data['_id'] = _id
        return self.type(data)
    def update(self, **data):
        self.collection.update({'_id': data['_id']}, data)
        print "** Update ! ** %s" % str(data)
    def remove(self, **data):
        self.collection.remove(data)

