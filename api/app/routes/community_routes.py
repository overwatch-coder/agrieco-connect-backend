from flask import Blueprint
from flask_restful import Api
from app.resources.community import CommunitiesGETResource, CommunityResource, CommunitiesPOSTResource, CommunityGETMembersResource, CommunityPUTMembersResource, CommunityGETMyCommunitiesResource, CommunityFeedsResource

bp = Blueprint('community', __name__)
api = Api(bp)

api.add_resource(CommunitiesGETResource, '/communities')
api.add_resource(CommunityResource, '/communities', '/communities/<int:id>')
api.add_resource(CommunitiesPOSTResource, '/communities')
api.add_resource(CommunityGETMembersResource, '/communities/<int:id>/members')
api.add_resource(CommunityPUTMembersResource, '/communities/<int:id>/members')
api.add_resource(CommunityGETMyCommunitiesResource, '/communities/my-communities')
api.add_resource(CommunityFeedsResource, '/communities/<int:id>/feeds')