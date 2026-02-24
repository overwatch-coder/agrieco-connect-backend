from flask import Blueprint
from flask_restful import Api
from api.app.resources.topic import TopicsGETResource, TopicResource, TopicsPOSTResource

bp = Blueprint('topic', __name__)
api = Api(bp)

api.add_resource(TopicsGETResource, '/topics')
api.add_resource(TopicResource, '/topics', '/topics/<int:id>')
api.add_resource(TopicsPOSTResource, '/topics')
