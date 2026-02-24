from api.app import db, bcrypt
from datetime import datetime, timedelta
from random import choice

# Define the association table for the many-to-many relationship between User and Topic
user_topics = db.Table('user_topics',
                       db.Column('user_id', db.Integer, db.ForeignKey(
                           'users.id'), primary_key=True),
                       db.Column('topic_id', db.Integer, db.ForeignKey(
                           'topics.id'), primary_key=True)
                       )

# Define the association table for the many-to-many relationship between Feed and Topic
feed_topics = db.Table('feed_topics',
                       db.Column('feed_id', db.Integer, db.ForeignKey(
                           'feeds.id'), primary_key=True),
                       db.Column('topic_id', db.Integer, db.ForeignKey(
                           'topics.id'), primary_key=True)
                       )

feed_likes = db.Table('feed_likes',
                      db.Column('feed_id', db.Integer, db.ForeignKey(
                          'feeds.id'), primary_key=True),
                      db.Column('user_id', db.Integer, db.ForeignKey(
                          'users.id'), primary_key=True)
                      )

user_communities = db.Table('user_communities',
                            db.Column('user_id', db.Integer, db.ForeignKey(
                                'users.id'), primary_key=True),
                            db.Column('community_id', db.Integer, db.ForeignKey(
                                'communities.id'), primary_key=True)
                            )

follows = db.Table('follows',
                   db.Column('follower_id', db.Integer, db.ForeignKey(
                       'users.id'), primary_key=True),
                   db.Column('followed_id', db.Integer, db.ForeignKey(
                       'users.id'), primary_key=True)
                   )

event_attendees = db.Table('event_attendees',
                           db.Column('event_id', db.Integer, db.ForeignKey(
                               'events.id'), primary_key=True),
                           db.Column('user_id', db.Integer, db.ForeignKey(
                               'users.id'), primary_key=True)
                           )


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    fullname = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    feeds = db.relationship('Feed', backref='user', lazy=True)
    events = db.relationship('Event', backref='user', lazy=True)
    role = db.Column(db.String(80), nullable=False, default='user')
    reset_code = db.Column(db.String(32), nullable=True)
    reset_code_expires_at = db.Column(db.DateTime, nullable=True)
    products = db.relationship('Product', backref='user', lazy=True)
    interested_topics = db.relationship('Topic', secondary=user_topics, backref=db.backref(
        'interested_users', lazy=True), lazy=True)
    likes = db.relationship('Feed', secondary=feed_likes, backref=db.backref(
        'liked_by', lazy='dynamic'), overlaps="liked_by,likes")
    password_hash = db.Column(db.String(128), nullable=False)

    following = db.relationship(
        'User', secondary=follows,
        primaryjoin=id == follows.c.follower_id,
        secondaryjoin=id == follows.c.followed_id,
        # Changed 'followed_by' to 'followers'
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    def __init__(self, fullname, username, email, password):
        self.username = username
        self.fullname = fullname
        self.email = email
        self.password_hash = self.get_hashed_password(password)

    def get_hashed_password(self, password):
        hash = bcrypt.generate_password_hash(password).decode('utf-8')
        return hash

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_reset_code(self):
        code = ''.join(choice(
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(32))
        self.reset_code = code
        self.reset_code_expires_at = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()
        return code

    def check_reset_code(self, code):
        if self.reset_code == code and self.reset_code_expires_at > datetime.utcnow():
            return True
        return False

    def serialize(self):
        return {
            "id": self.id,
            "fullname": self.fullname if self.fullname else "",
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "interested_topics": [topic.serialize() for topic in self.interested_topics],
            "owned_communities": [community.serialize() for community in self.owned_communities],
            "member_communities": [community.serialize() for community in self.member_communities]
        }

    def serialize_with_token(self, token):
        return {
            "id": self.id,
            "fullname": self.fullname if self.fullname else "",
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "interested_topics": [topic.serialize() for topic in self.interested_topics],
            "token": token
        }

    def serialize_less_sensitive(self):
        return {
            "id": self.id,
            "fullname": self.fullname if self.fullname else "",
            "username": self.username,
            "email": self.email,
            "followers": self.followers.count(),  # Changed 'followed_by' to 'followers'
        }

    def followUnfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)
        else:
            self.following.append(user)
        db.session.commit()

    def is_following(self, user):
        return self.following.filter(follows.c.followed_id == user.id).count() > 0


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    feeds = db.relationship('Feed', secondary=feed_topics, backref=db.backref(
        'feed_topics', lazy=True), lazy=True, overlaps="feed_topics,feeds")

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }


class Feed(db.Model):
    __tablename__ = 'feeds'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey(
        'communities.id'), nullable=True)  # Allow null for feeds not under a community
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    topics = db.relationship('Topic', secondary=feed_topics, backref=db.backref(
        'topic_feeds', lazy=True), lazy=True, overlaps="feed_topics,feeds")
    comments = db.relationship('Comment', backref='feed', lazy=True)
    likes = db.relationship('User', secondary=feed_likes, backref=db.backref(
        'liked_feeds', lazy='dynamic'), overlaps="liked_by,likes")
    community = db.relationship('Community', backref=db.backref(
        'feeds', lazy=True))  # Relationship to Community

    def __repr__(self):
        return f'<Feed {self.id}>'

    def __init__(self, content, user_id, images=None):
        self.content = content
        self.user_id = user_id
        self.images = images

    def serialize(self):
        return {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "images": self.images,
            "is_active": self.is_active,
            "topics": [topic.serialize() for topic in self.topics],
            "likes": [user.serialize_less_sensitive() for user in self.likes],
            "comments": [comment.serialize() for comment in self.comments]
        }


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feed_id = db.Column(db.Integer, db.ForeignKey('feeds.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, content, user_id, feed_id):
        self.content = content
        self.user_id = user_id
        self.feed_id = feed_id

    def serialize(self):
        return {
            "id": self.id,
            "content": self.content,
            "user": User.query.get(self.user_id).serialize_less_sensitive(),
            "feed_id": self.feed_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": self.is_active
        }


class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feed_id = db.Column(db.Integer, db.ForeignKey('feeds.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    def __init__(self, user_id, feed_id):
        self.user_id = user_id
        self.feed_id = feed_id

    def serialize(self):
        return {
            "id": self.id,
            "user": User.query.get(self.user_id).serialize_less_sensitive(),
            "feed_id": self.feed_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.Text, nullable=True)
    seller_information = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, name, price, user_id, seller_information=None, description=None, image=None):
        self.name = name
        self.price = price
        self.description = description
        self.user_id = user_id
        self.image = image
        self.seller_information = seller_information

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image": self.image,
            "seller_information": self.seller_information,
            "user_id": self.user_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": self.is_active
        }


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.String(80), nullable=False)
    end_time = db.Column(db.String(80), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(120), nullable=True)
    price = db.Column(db.Float, nullable=True)
    image = db.Column(db.Text, nullable=True)
    attendees = db.relationship('User', secondary=event_attendees, backref=db.backref(
        'attending_events', lazy=True), lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, title, start_time, end_time, start_date, location, user_id, description=None, price=None, image=None):
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.start_date = start_date
        self.location = location
        self.price = price
        self.image = image
        self.user_id = user_id

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.start_date.strftime("%Y-%m-%d"),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "price": self.price,
            "location": self.location,
            "image": self.image,
            "user": User.query.get(self.user_id).serialize_less_sensitive(),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": self.is_active
        }


class Community(db.Model):
    __tablename__ = 'communities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    category = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('User', backref='owned_communities', lazy=True)
    members = db.relationship('User', secondary=user_communities, backref=db.backref(
        'member_communities', lazy=True), lazy=True)
    # feeds = db.relationship('Feed', backref='community', lazy=True)

    def __init__(self, name, owner_id, description=None, category=None, location=None):
        self.name = name
        self.owner_id = owner_id
        self.description = description
        self.category = category
        self.location = location

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "location": self.location,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": self.is_active,
            "owner": self.owner.serialize_less_sensitive(),
            "members_count": len(self.members),
            "member_ids": [member.id for member in self.members]
        }


class AppointmentAvailability(db.Model):
    __tablename__ = 'appointment_availabilities'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(80), nullable=True)
    specialty = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    experience_level = db.Column(db.String(80), nullable=True)
    availability_slot_start = db.Column(db.DateTime, nullable=True)
    availability_slot_end = db.Column(db.DateTime, nullable=True)
    contact_information = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    is_booked = db.Column(db.Boolean, nullable=False, default=False)
    booked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, user_id, availability_slot_start, availability_slot_end, company_name=None, specialty=None, location=None, experience_level=None, contact_information=None, bio=None):
        self.user_id = user_id
        self.company_name = company_name
        self.specialty = specialty
        self.location = location
        self.experience_level = experience_level
        self.availability_slot_start = availability_slot_start
        self.availability_slot_end = availability_slot_end
        self.contact_information = contact_information
        self.bio = bio

    def serialize(self):
        return {
            "id": self.id,
            "user": User.query.get(self.user_id).serialize_less_sensitive(),
            "company_name": self.company_name,
            "specialty": self.specialty,
            "location": self.location,
            "experience_level": self.experience_level,
            "availability_slot_start": self.availability_slot_start.strftime("%Y-%m-%d %H:%M:%S"),
            "availability_slot_end": self.availability_slot_end.strftime("%Y-%m-%d %H:%M:%S"),
            "contact_information": self.contact_information,
            "bio": self.bio,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": self.is_active,
            "is_booked": self.is_booked
        }


class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
