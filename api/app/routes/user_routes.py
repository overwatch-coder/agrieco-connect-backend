from flask import Blueprint
from flask_restful import Api
from app.resources.user import UserResource, UsersGETResource, UserFollowResource, UserFollowingResource, UserAppointmentsResource

bp = Blueprint('user', __name__)
api = Api(bp)

api.add_resource(UsersGETResource, '/users')
api.add_resource(UserResource, '/users', '/users/<int:id>')
api.add_resource(UserFollowResource, '/users/<int:id>/follow')
api.add_resource(UserFollowingResource, '/users/following')
api.add_resource(UserAppointmentsResource, '/users/appointments')