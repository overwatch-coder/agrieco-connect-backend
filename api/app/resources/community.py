from flask_restful import Resource
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.app import db
from api.app.models import Community, Feed, User


class CommunitiesGETResource(Resource):
    def get(self):
        return [community.serialize() for community in Community.query.all()]


class CommunitiesPOSTResource(Resource):
    def post(self):
        # Applying decorator directly and calling wrapped method
        result = jwt_required()(self._post)()
        return result

    def _post(self):
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            name = data.get('name')
            description = data.get('description')
            location = data.get('location')
            category = data.get('category')
            new_community = Community(
                name=name, description=description, location=location, category=category, owner_id=user_id)
            # add user to community
            user = User.query.get(user_id)
            new_community.members.append(user)
            db.session.add(new_community)
            db.session.commit()
            return new_community.serialize(), 201
        except Exception as e:
            print("Error: ", e)
            return {"message": "Invalid request"}, 400


class CommunityResource(Resource):
    def get(self, id):
        community = Community.query.get(id)
        if community:
            return community.serialize()
        return None

    @jwt_required()
    def put(self, id):
        try:
            user_id = get_jwt_identity()
            community = request.json
            _community = Community.query.get(id)
            if _community:
                if _community.owner_id != user_id:
                    return {"message": "You are not authorized to perform this action"}, 403
                _community.name = community["name"]
                _community.description = community["description"]
                _community.location = community["location"]
                _community.category = community["category"]
                db.session.commit()
                return _community.serialize()
            return None
        except Exception as e:
            print("Error: ", e)
            return {"message": "Invalid request"}, 400

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        community = Community.query.get(id)
        if community:
            if community.owner_id != user_id:
                return {"message": "You are not authorized to perform this action"}, 403
            db.session.delete(community)
            db.session.commit()
            return "", 204
        return None


class CommunityGETMembersResource(Resource):
    def get(self, id):
        community = Community.query.get(id)
        if community:
            return [member.serialize() for member in community.members]
        return None


class CommunityPUTMembersResource(Resource):
    @jwt_required()
    def put(self, id):
        user_id = get_jwt_identity()
        community = Community.query.get(id)
        if community:
            if user_id:
                user = User.query.get(user_id)
                if not user:
                    return {"message": "User not found"}, 404
                community.members.append(user)
                db.session.commit()
                return {"message": "User added to community"}, 200
        return None


class CommunityGETMyCommunitiesResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return {"message": "User not found"}, 404

        member_communities = [community.serialize()
                              for community in user.member_communities]
        return jsonify(member_communities)


class CommunityFeedsResource(Resource):
    @jwt_required(optional=True)
    def get(self, id):
        community = Community.query.get(id)
        if not community:
            return {"message": "Community not found"}, 404

        feeds = Feed.query.filter_by(community_id=id).order_by(
            Feed.created_at.desc()).all()
        return jsonify([feed.serialize() for feed in feeds])
