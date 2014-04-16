import bottle

def make_route_callback(callback):
    if type(callback) == list: callback = partial(*callback)
    def wrapper(**context):
        return callback(**get_session(**start_context(**context)))
    return wrapper

for route in routes.items():
    path, callback = route
    if path.startswith('#'):
        bottle.post(path[1:])(make_route_callback(callback))
    elif path.startswith('X'):
        bottle.delete(path[1:])(make_route_callback(callback))
    elif path.startswith('>'):
        bottle.put(path[1:])(make_route_callback(callback))
    else:
        bottle.get(path)(make_route_callback(callback))

bottle.debug(config.debug)
bottle.run(server=config.server, host='0.0.0.0', port=80, reloader=config.debug)
