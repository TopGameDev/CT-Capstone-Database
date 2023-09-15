from . import api
from app import db
from app.models import Post, User
from flask import request
from .auth import basic_auth, token_auth



@api.route('/token')
@basic_auth.login_required
def get_token():
    auth_user = basic_auth.current_user()
    token = auth_user.get_token()
    return {
        'token': token,
        'tokenExpiration': auth_user.token_expiration
    }

@api.route('/posts')
def get_posts():
    posts = db.session.execute(db.select(Post)).scalars().all()
    return [post.to_dict() for post in posts]

@api.route('/posts/<post_id>')
def get_post(post_id):
    post = db.session.get(Post, post_id)
    if post:
        return post.to_dict()
    else:
        return {'error': f'Post with an ID of {post_id} does not exist.'}, 404


@api.route('/posts', methods=["POST"])
@token_auth.login_required
def create_post():
    print(request)
    # Check to see that the request body is JSON
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    # Get the data from the request body
    data = request.json
    print(data, type(data))
    # Validate incoming data
    required_fields = ['title', 'body']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be in the request body"}, 400

    # Get the data from the body
    title = data.get('title')
    body = data.get('body')
    image_url = data.get('image_url')


    current_user = token_auth.current_user()
    # Create a new post instance with the data
    new_post = Post(title=title, body=body, image_url=image_url, user_id=current_user.id)
    # add to the database
    db.session.add(new_post)
    db.session.commit()

    return new_post.to_dict(), 201


@api.route('/posts/<post_id>', methods=['PUT'])
@token_auth.login_required
def edit_post(post_id):
    # Check to make sure there is a JSON request body
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    # Get the post from the db
    post = db.session.get(Post, post_id)
    if post is None:
        return {'error': f"Post with an ID of {post_id} not found"}, 404
    # Make sure post authenticated user is the post author
    current_user = token_auth.current_user()
    if post.author != current_user:
        return {'error': 'You do not have permission to edit this post'}, 403
    # Update the post with changes
    data = request.json
    for field in data:
        if field in {'title','body', 'image_url'}:
            setattr(post, field, data[field])
    db.session.commit()
    return post.to_dict()

@api.route('/posts/<post_id>', methods=['DELETE'])
@token_auth.login_required
def delete_post(post_id):
    # Get the post from the db
    post = db.session.get(Post, post_id)
    if post is None:
        return {'error': f'Post with an ID of {post_id} does not exist!'}, 404
    # Make sure post authenticated user is the post author
    current_user = token_auth.current_user()
    if post.author != current_user:
        return {'error': "You do not have permission to delete this post"}, 403
    # Delete Post
    db.session.delete(post)
    db.session.commit()
    return {'succes': f"'{post.title}' has been deleted!"}


@api.route('/users/me')
@token_auth.login_required
def get_me():
    me = token_auth.current_user()
    return me.to_dict()


@api.route('/users', methods=['POST'])
def create_user():
    print(request)
    # Check to see that the request body is JSON
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    # Get the data from the request body
    data = request.json
    print(data, type(data))
    # Validate incoming data
    required_fields = ['firstName', 'lastName', 'username', 'email', 'password']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be in the request body"}, 400

    # Get the data from the body
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Check if a user with that username or email already exists
    check_user = db.session.execute(db.select(User).where((User.username == username) | (User.email == email))).scalar()
    if check_user:
        return {'error': f"A user with that username and/or email already exists"}, 400

    # Create a new post instance with the data
    new_user = User(first_name = first_name, last_name = last_name, username = username, email = email, password = password)
    # add to the database
    db.session.add(new_user)
    db.session.commit()

    return new_user.to_dict(), 201