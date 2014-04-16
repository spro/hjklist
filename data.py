import string
import random
from meta_data import *
import config

conn = pymongo.Connection(host=config.db_host)
db = conn.hjklist

class User(Document):
    pass

class Users(Collection):
    collection = db.users
    type = User
    def auth(self, username, password):
        return self.get(username=username, password=password, deactivated={'$exists': False})

token_chars = string.ascii_letters + string.digits
def generate_token(size=10):
    return ''.join(random.choice(token_chars) for x in range(size))

users = Users()
users.collection.ensure_index('username')

class Session(Document):
    types = {
        'messages': list
    }
    def add_message(self, text):
        self.messages.append(text)
        sessions.update(**self)
    @property
    def user(self):
        return users.get(_id=self['user'])

class Sessions(Collection):
    collection = db.sessions
    type = Session

sessions = Sessions()
sessions.collection.ensure_index('user')
sessions.collection.ensure_index('token')

class Edge(Document): 
    @property
    def to_(self): return nodes.get(_id=self['to_'])
    @property
    def from_(self): return nodes.get(_id=self['from_'])

class Edges(Collection):
    collection = db.edges
    type = Edge
    def to_(self, node): return self.fetch(to_=node.id)
    def from_(self, node): return self.fetch(from_=node.id)

class Node(Document):
    def __init__(self, *args, **kwargs):
        Document.__init__(self, *args, **kwargs)
        #self['items'] = self.to_
    def get_to_(self): return [e.to_ for e in edges.from_(self)]
    def set_to_(self, other):
        edges.new(from_=self.id, to_=other.id)
    to_ = property(get_to_, set_to_)
    def get_from_(self): return [e.from_ for e in edges.from_(self)]
    def set_from_(self, other):
        edges.new(to_=self.id, from_=other.id)
    from_ = property(get_from_, set_from_)
    @property
    def from_(self): return [e.from_ for e in edges.to_(self)]

class Nodes(Collection):
    collection = db.nodes
    type = Node

edges = Edges()
edges.collection.ensure_index('to_')
edges.collection.ensure_index('from_')
nodes = Nodes()
nodes.collection.ensure_index('user')
nodes.collection.ensure_index('name')

def make_node_rep(node, item_levels=0):
    node_rep = node.copy()
    node_rep['_id'] = node.id_str
    if item_levels:
        node_rep = add_node_rep_items(node, node_rep, item_levels-1)
    return node_rep

def add_node_rep_items(node, node_rep, item_levels=0):
    new_node_rep = node_rep.copy()
    node_items = node.to_
    new_items = []
    for item in node_items:
        item_rep = make_node_rep(item, item_levels)
        new_items.append(item_rep)
    if len(new_items) > 0: new_node_rep['items'] = new_items
    return new_node_rep

