from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.app import db
from .auth import check_if_user_is_admin
from api.app.models import Topic


class TopicsGETResource(Resource):
    def get(self):
        return [topic.serialize() for topic in Topic.query.all()]


class TopicsPOSTResource(Resource):
    def post(self):
        # Applying decorator directly and calling wrapped method
        result = jwt_required()(self._post)()
        return result

    def _post(self):
        user_id = get_jwt_identity()
        if not check_if_user_is_admin(user_id):
            return {"message": "You are not authorized to perform this action"}, 403
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        new_topic = Topic(name=name, description=description)
        db.session.add(new_topic)
        db.session.commit()
        return new_topic.serialize(), 201


class TopicResource(Resource):
    def get(self, id):
        topic = Topic.query.get(id)
        if topic:
            return topic.serialize()
        return None

    @jwt_required()
    def put(self, id):
        user_id = get_jwt_identity()
        if not check_if_user_is_admin(user_id):
            return {"message": "You are not authorized to perform this action"}, 403
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        topic = Topic.query.get(id)
        if topic:
            topic.name = name
            topic.description = description
            db.session.commit()
            return topic.serialize()
        return None

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        if not check_if_user_is_admin(user_id):
            return {"message": "You are not authorized to perform this action"}, 403
        topic = Topic.query.get(id)
        if topic:
            db.session.delete(topic)
            db.session.commit()
            return "", 204
        return None
