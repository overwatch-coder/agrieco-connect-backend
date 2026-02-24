from flask_restful import Resource
from flask import request, jsonify
from sqlalchemy import func
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.app.resources.auth import check_if_user_is_admin
from api.app import db
from api.app.models import Feed, Topic, User, Comment
import os
import re
from api.app.cloudinary import upload_image
from api.app.trendingbot import TrendingKeywords
from datetime import datetime

# Configure Flask-Uploads
# photos = UploadSet('photos', IMAGES)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Configure the upload set to save uploaded files to a specific directory
UPLOAD_FOLDER = 'public/uploads/feed_images'
# configure_uploads(app, photos)


def secure_filename(filename):
    filename = re.sub(r'[^A-Za-z0-9_.-]', '_', filename)
    return filename


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class FeedsGETResource(Resource):
    @jwt_required(optional=True)
    def get(self):
        # i want to return all feeds sorted by date in descending order if user is not logged in and logged in user we only return feeds that are associated with the topics they are interested in
        user_id = get_jwt_identity()
        random_fact = TrendingKeywords().get_random_facts()
        random_feed = Feed(content=random_fact, images=None, user_id=None)
        random_feed.created_at = datetime.utcnow()
        random_feed.updated_at = datetime.utcnow()
        if user_id:
            user = User.query.get(user_id)
            topics = user.interested_topics
            feeds = Feed.query.filter(Feed.topics.any(Topic.id.in_(
                [topic.id for topic in topics]))).order_by(Feed.created_at.desc()).all()
            feeds.insert(0, random_feed)
        else:
            feeds = Feed.query.order_by(Feed.created_at.desc()).all()
            feeds.insert(0, random_feed)
        return [feed.serialize() for feed in feeds]


class FeedResource(Resource):
    def get(self, id):
        feed = Feed.query.get(id)
        if feed:
            return feed.serialize()
        return None

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        if not user_id:
            return {"message": "Unauthorized"}, 401

        # Check if files are in the request
        # if 'photo' not in request.files:
        #     return {"message": "No file part"}, 400

        # Retrieve list of uploaded files
        photos = request.files.getlist('photo')

        # Ensure the upload folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # Initialize list to store file paths
        uploaded_files = []

        for photo in photos:
            if photo.filename == '':
                return {"message": "No selected file"}, 400

            if photo and allowed_file(photo.filename):
                file_path = upload_image(photo)
                uploaded_files.append(file_path)

        # Handle other form data
        content = request.form.get('content')
        topics_str = request.form.get('topics')
        community_id = request.form.get('community_id') or None

        # Split the topics string by commas and convert to integers
        topics_ids = [int(topic_id.strip())
                      for topic_id in topics_str.split(',')] if topics_str else []

        new_feed = Feed(content=content, user_id=user_id,
                        images=",".join(uploaded_files))
        new_feed.community_id = community_id

        # Associate topics with the feed
        if topics_ids:
            topics = Topic.query.filter(Topic.id.in_(topics_ids)).all()
            new_feed.topics.extend(topics)

        db.session.add(new_feed)
        db.session.commit()

        return new_feed.serialize(), 201

    @jwt_required()
    def put(self, id):
        user_id = get_jwt_identity()
        if not user_id:
            return {"message": "Unauthorized"}, 401

        feed = request.json
        _feed = Feed.query.get(id)

        if _feed:
            if _feed.user_id != user_id:
                return {"message": "You are not authorized to perform this action"}, 403
            _feed.content = feed["content"]
            _feed.user_id = user_id
            _feed.images = feed["images"]
            if "topics" in feed:
                topics = Topic.query.filter(Topic.id.in_(feed["topics"])).all()
                _feed.topics = topics
            db.session.commit()
            return _feed.serialize()
        return jsonify({"message": "Feed could not be updated"}), 500

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        if not user_id:
            return {"message": "Unauthorized"}, 401
        feed = Feed.query.get(id)
        if feed:
            if feed.user_id != user_id:
                return {"message": "You are not authorized to perform this action"}, 403
            db.session.delete(feed)
            db.session.commit()
            return "", 204
        return jsonify({"message": "Feed could not be deleted"}), 500


class FeedCommentsResource(Resource):
    @jwt_required(optional=True)
    def get(self, id):
        feed = Feed.query.get(id)
        if feed:
            return [comment.serialize() for comment in feed.comments]
        return None

    @jwt_required()
    def post(self, id):
        user_id = get_jwt_identity()
        if not user_id:
            return {"message": "Unauthorized"}, 401
        feed = Feed.query.get(id)
        if feed:
            data = request.get_json()
            content = data.get('content')
            new_comment = Comment(content=content, user_id=user_id, feed_id=id)
            db.session.add(new_comment)
            db.session.commit()
            return new_comment.serialize(), 201
        return jsonify({"message": "Feed not found"}), 404


class FeedLikesResource(Resource):
    @jwt_required()
    def put(self, id):
        user_id = get_jwt_identity()
        if not user_id:
            return {"message": "Unauthorized"}, 401
        feed = Feed.query.get(id)
        if feed:
            user = User.query.get(user_id)
            if user in feed.likes:
                feed.likes.remove(user)
            else:
                feed.likes.append(user)
            db.session.commit()
            return feed.serialize()
        return jsonify({"message": "Feed not found"}), 404

    def get(self, id):
        feed = Feed.query.get(id)
        if feed:
            return [like.serialize() for like in feed.likes]
        return None


class FeedTrendingResource(Resource):
    def get(self):
        feeds = Feed.query.all()
        feed_contents = [feed.content for feed in feeds]
        trending_keywords = TrendingKeywords().get_trending_keywords(feed_contents)
        # return trending_keywords

        # Get feeds with most likes
        most_liked_feeds = db.session.query(
            Feed, func.count('feed_likes.c.user_id').label('like_count')
        ).outerjoin(Feed.likes).group_by(Feed.id).order_by(func.count('feed_likes.c.user_id').desc()).limit(5).all()

        # Get feeds with most comments
        most_commented_feeds = db.session.query(
            Feed, func.count('comments.id').label('comment_count')
        ).outerjoin(Feed.comments).group_by(Feed.id).order_by(func.count('comments.id').desc()).limit(5).all()

        # Combine the feeds, ensuring no duplicates
        feed_ids = {feed.id for feed,
                    _ in most_liked_feeds + most_commented_feeds}
        feeds = db.session.query(Feed).filter(Feed.id.in_(feed_ids)).all()

        # Extract the feed contents
        feed_contents = [feed.content for feed in feeds]

        # Get the trending keywords
        trending_keywords = TrendingKeywords().get_trending_keywords(feed_contents)

        return jsonify(trending_keywords)


class FeedsGETByTopicResource(Resource):
    @jwt_required(optional=True)
    def get(self, topic_name):
        topics = Topic.query.filter(func.lower(
            Topic.name).contains(topic_name.lower())).all()

        feeds = Feed.query.filter(Feed.topics.any(Topic.id.in_(
            [topic.id for topic in topics]))).order_by(Feed.created_at.desc()).all()

        filtered_feeds = [feed.serialize() for feed in feeds if any(
            topic_name.lower() in topic.name.lower() for topic in feed.topics)]

        return filtered_feeds


class CommunityFeedsGETResource(Resource):
    @jwt_required()
    def get(self, community_id):
        feeds = Feed.query.filter_by(community_id=community_id).order_by(
            Feed.created_at.desc()).all()
        return [feed.serialize() for feed in feeds]
