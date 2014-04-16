import bottle
from data import *
from functools import partial
import config

class Context(Document): pass

def message(message_text, **context):
    context['message'] = message_text
    return render('message', **context)

def start_context(**context):
    context['messages'] = []
    context['errors'] = []
    context['submitted'] = defaultdict(str)
    context['timestamp'] = time.time()
    context['config'] = config
    return context

def get_session(**context):
    context['session'] = None
    context['user'] = None
    session_user = bottle.request.get_cookie("user", secret=config.secret)
    session_token = bottle.request.get_cookie("token", secret=config.secret)
    if session_user and session_token:
        session = sessions.get(user=session_user, token=session_token)
        if session:
            context['session'] = session
            context['user'] = session.user
            return context
    return context

def authenticate(f, **context):
    if context['session'] and context['user']:
        return f(**context)
    return bottle.redirect('/login?next=%s' % bottle.request.path)

def render(template, **context):
    return bottle.jinja2_template(template, **context)

def renderer(template, **base_context):
    def wrapper(**context):
        return render(template, **dict(base_context.items() + context.items()))
    return wrapper
