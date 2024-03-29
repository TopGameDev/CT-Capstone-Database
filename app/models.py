import os
import base64
from app import db, login
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from random import randint
from flask_login import UserMixin


# DDL Statement
# CREATE TABLE user(
#   id SERIAL PRIMARY KEY,
#   first_name VARCHAR(50) NOT NULL,
# )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(75), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False, unique=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', cascade="delete") # The backref is how we create a list inside of another list with the User info (line 88-97)
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    # Hash Password taken from User
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.password = generate_password_hash(kwargs.get('password'))

    def __repr__(self):
        return f"<User {self.id}|{self.username}>"
    
    # Validate Password
    def check_password(self, password_guess):
        return check_password_hash(self.password, password_guess)
    
    def get_token(self, expires_in=3600):
        # Set the start of the timer
        now = datetime.utcnow()
        # Check for how long token has been active
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        # Create Token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        # Set Token Expiration
        self.token_expiration = now + timedelta(seconds=expires_in)
        # Save Token to database and Execute
        db.session.commit()
        return self.token
    
    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()

    # Create a dictionary out of the Data
    def to_dict(self):
        return {
            'id': self.id,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'email': self.email,
            'username': self.username
        }

@login.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

def random_photo():
    return f"https://picsum.photos/500?random={randint(1,100)}"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, nullable=False, default=random_photo)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # SQL - FOREIGN KEY(user_id) REFERENCES user(id)

    def __repr__(self):
        return f"<Post {self.id}|{self.title}>"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'imageUrl': self.image_url,
            'dateCreated': self.date_created,
            'userId': self.user_id,
            'author': self.author.to_dict()
        }
