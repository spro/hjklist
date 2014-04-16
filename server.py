import bottle
import pymongo
import json
from meta_server import *
from data import *
from utils import *

#-----
# Main views
#-----

def index(**context):
    session = context['session']
    if session and session.user:
        root = nodes.get(user=session.user.id, name='root')
        if not root:
            root = nodes.new(user=session.user.id, name='root')
        if len(root.to_) < 1:
            welcome_node = nodes.new(user=session.user.id, name='Welcome.')
            root.to_ = welcome_node
        root['items'] = root.to_
        context['root'] = pymongo_to_json(make_node_rep(root, 2))
        return render('list', **context)
    else:
        return render('home', **context)

login_form = renderer('login')
def do_login(**context):
    context['submitted']['username'] = username = bottle.request.forms.get('username')
    context['submitted']['password'] = password = bottle.request.forms.get('password')
    if username and password:
        print 'trying with %s and %s' % (username, password)
        user = users.auth(username, password)
        if user:
            token = generate_token()
            sessions.new(user=user.id, token=token)
            bottle.response.set_cookie("user", user.id, secret=config.secret)
            bottle.response.set_cookie("token", token, secret=config.secret)
            if bottle.request.query.next:
                return bottle.redirect(bottle.request.query.next)
            return bottle.redirect("/")
        else:
            context['errors'].append("Incorrect username or password.")
            print users.fetch()
            print db
            return login_form(**context)
    return login_form(**context)

def logout(**context):
    if context['session']:
        session = context['session']
        sessions.remove(user=session.user.id)
        bottle.response.delete_cookie("user", secret=config.secret)
        bottle.response.delete_cookie("token", secret=config.secret)
    return bottle.redirect('/login')

signup_form = renderer('signup')
def do_signup(**context):
    session = context['session']
    context['submitted']['username'] = username = bottle.request.forms.get('username') or ''
    context['submitted']['email'] = email = bottle.request.forms.get('email') or ''
    password = bottle.request.forms.get('password')
    if bottle.request.forms:
        if not username: context['errors'].append("Please enter a username.")
        elif users.exists(username=username): context['errors'].append("This username is in use.")
        if not email: context['errors'].append("Please enter an email address.")
        elif users.exists(email=email): context['errors'].append("This email address is in use.")
        if not password: context['errors'].append("Please enter a password.")
        if len(context['errors']) > 0:
            return signup_form(**context)
        # Set up new user
        verification_code = generate_token(20)
        user = users.new(
            username=username,
            password=password,
            email=email,
            verification=verification_code,
        )
        verification_url = config.base_url + "/verify?user=%s&code=%s" % (username, verification_code)
        # Set them up a root node
        user_root = nodes.new(user=user.id, name='root')
        welcome = nodes.new(name='Welcome to hjklist!')
        user_root.to_ = welcome
        # Send some mail
        send_mail(user.email, 'hjklist@gmail.com', 'Welcome to hjklist!', 
            'Verify your email address by visiting: %s' % verification_url,
            'Verify your email address by visiting: <a href="%s">%s</a>' % (verification_url, verification_url))
        context['messages'].append("Thank you for signing up. Please check your email for a verification link.")
        return login_form(**context)
    else:
        return signup_form(**context)

#-----
# Account
#-----

account = renderer('account')
confirm_deactivate_account = renderer('deactivate_account')
update_password_form = renderer('update_password_form')
forgot_password_form = renderer('forgot_password_form')
reset_password_form = renderer('reset_password_form')

def update_password(**context):
    session = context['session']
    old_password = bottle.request.forms.get('old_password')
    new_password = bottle.request.forms.get('new_password')
    new_password_confirm = bottle.request.forms.get('new_password_confirm')
    if old_password == session.user.password:
        if new_password == new_password_confirm:
            session.user['password'] = new_password
            users.update(**session.user)
            context['messages'].append("Successfully updated password.")
            return account(**context)
        else:
            context['errors'].append("Passwords do not match.")
    else:
        context['errors'].append("Incorrect old password.")
    return update_password_form(**context)

def forgot_password(**context):
    if bottle.request.forms:
        email = bottle.request.forms.get('email')
        token = bottle.request.forms.get('token')
        if email:
            user = users.get(email=email)
            if user:
                reset_password_token = generate_token(20)
                user['reset_password_token'] = reset_password_token
                users.update(**user)
                reset_password_url = config.base_url + '/account/password/reset?email=%s&token=%s' % (email, reset_password_token)
                send_mail(user.email, 'hjklist@gmail.com', 'Reset your hjklist password', 
                    'Set your new password at: %s' % reset_password_url,
                    'Set your new password at: <a href="%s">%s</a>' % (reset_password_url, reset_password_url))
                return message("Check your email for the link where you can reset your password.")
            else:
                return message("Sorry, we couldn't find your account.")    
    return forgot_password_form(**context)

def reset_password(**context):
    email = bottle.request.query.get('email')
    token = bottle.request.query.get('token')
    password = bottle.request.forms.get('password')
    confirm_password = bottle.request.forms.get('confirm_password')
    if email and token:
        user = users.get(email=email)
        if user and user.reset_password_token == token:
            if bottle.request.forms:
                if password and password == confirm_password:
                    user['password'] = password
                    users.update(**user)
                    context['messages'].append("Successfully updated password.")
                    return login_form(**context)
                else:
                    context['messages'].append("Passwords must match.")
                    return reset_password_form(**context)
        else:
            context['messages'].append("Password reset token invalid.")
    else:
        context['messages'].append("Verification code invalid.")
    return reset_password_form(**context)

def deactivate_account(**context):
    session = context['session']
    user = session.user
    user['deactivated'] = True
    users.update(**user)
    sessions.remove(user=session.user.id)
    bottle.response.delete_cookie("user", secret=session_secret)
    bottle.response.delete_cookie("token", secret=session_secret)
    return bottle.redirect('/')

#-----
# Node views
#-----

def show_node(node_id, **context):
    session = context['session']
    node = nodes.get(user=session.user.id, _id=node_id)
    node_rep = make_node_rep(node, 2)
    return pymongo_to_json(node_rep)

def new_node(**context):
    session = context['session']
    new_node = nodes.new(user=session.user.id, name=bottle.request.json.get('name'))
    from_node = nodes.get(user=session.user.id, _id=bottle.request.json.get('from_'))
    from_node.to_ = new_node
    return pymongo_to_json(make_node_rep(new_node))

def update_node(node_id, **context):
    session = context['session']
    node = nodes.get(user=session.user.id, _id=node_id)
    new_name = bottle.request.json.get('name')
    new_from_ = bottle.request.json.get('from_')
    if new_name:
        node['name'] = new_name
        nodes.update(**node)
    if new_from_:
        edges.remove(to_=node.id)
        from_node = nodes.get(_id=new_from_)
        node.from_ = from_node

def delete_node(node_id, **context):
    session = context['session']
    node = nodes.get(user=session.user.id, _id=node_id)
    edges.remove(to_=node.id)
    edges.remove(from_=node.id)
    nodes.remove(**node)

#-----
# Route configuration
#-----

_node_id_ = "<node_id:re:[a-zA-Z0-9]+>"
route_map = {
    '/': index,

    '/signup': signup_form,
    '#/signup': do_signup,
    '/login': login_form,
    '#/login': do_login,
    '/logout': logout,

    '/account': [authenticate, account],
    '/account/password': [authenticate, update_password_form],
    '#/account/password': [authenticate, update_password],
    '/account/password/forgot': forgot_password_form,
    '#/account/password/forgot': forgot_password,
    '/account/password/reset': reset_password,
    '#/account/password/reset': reset_password,
    '/account/deactivate': [authenticate, confirm_deactivate_account],
    '#/account/deactivate': [authenticate, deactivate_account],

    '#/new': [authenticate, new_node],
    '/'+_node_id_: [authenticate, show_node],
    '>/'+_node_id_: [authenticate, update_node],
    'X/'+_node_id_: [authenticate, delete_node],
}

# Define routes from the route map
def make_route_callback(callback):
    if type(callback) == list: callback = partial(*callback)
    def wrapper(**context):
        return callback(**get_session(**start_context(**context)))
    return wrapper

for route in route_map.items():
    path, callback = route
    if path.startswith('#'):
        bottle.post(path[1:])(make_route_callback(callback))
    elif path.startswith('X'):
        bottle.delete(path[1:])(make_route_callback(callback))
    elif path.startswith('>'):
        bottle.put(path[1:])(make_route_callback(callback))
    else:
        bottle.get(path)(make_route_callback(callback))

# Static fallback
@bottle.route('/<filepath:path>')
def static_file(filepath):
    return bottle.static_file(filepath, root='./static/')

# Run the server
bottle.debug(config.debug)
bottle.run(server=config.server, host='0.0.0.0', port=config.port, reloader=config.debug)

