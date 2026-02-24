from flask_restful import Resource
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from flask_mail import Message
from app import db, mail
from app.models import User, Topic
import os


users = [{"id": 1, "username": "user1", "email": "test@email.com", "password": "password"},
         {"id": 2, "username": "user2", "email": "test2@email.com", "password": "password"}]


class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "fullname": user.fullname,
            }
            # return jsonify({
            #     "access_token": access_token,
            #     "user": user_data
            # }), 200
            return {"user": user.serialize_with_token(access_token)}, 200
        return {"message": "Invalid credentials"}, 401


class ForgotPasswordResource(Resource):
    def post(self):
        data = request.get_json()
        email = data.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            msg = Message(subject="Password Reset",
                          sender="jossynationworld@gmail.com", recipients=[email])
            code = user.generate_reset_code()
            url = os.getenv('DOMAIN', 'http://localhost:5000') + \
                f"/reset-password?reset_code={code}"
            msg.body = f"Dear {user.username},\n\nHere is your password <a href=\"{url}\">reset link</a>\n\nBest regards,\nYour App Team"

            # Send email
            try:
                mail.send(msg)
                return {"message": "Password reset link sent to your email"}, 200
            except Exception as e:
                return {"message": "Failed to send email", "error": str(e)}, 500
        return {"message": "User not found"}, 404


class ResetPasswordResource(Resource):
    def post(self):
        code = request.args.get('reset_code')
        data = request.get_json()
        email = data.get('email')
        new_password = data.get('new_password')
        user = User.query.filter_by(email=email).first()

        if user:
            if not user.check_reset_code(code):
                return {"message": "Invalid reset code"}, 400

            user.password_hash = user.get_hashed_password(new_password)
            user.reset_code = None
            user.reset_code_expires_at = None
            # user.password = new_password
            db.session.commit()
            return {"message": "Password reset successful"}, 200
        return {"message": "User not found"}, 404


class RegisterResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        fullname = data.get('fullname')
        email = data.get('email')
        interested_topics_ids = data.get('interested_topics_ids')
        password = data.get('password')

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return {"message": "User already exists"}, 400

        new_user = User(fullname=fullname, username=username,
                        email=email, password=password)
        if interested_topics_ids:
            interested_topics = Topic.query.filter(
                Topic.id.in_(interested_topics_ids)).all()
            new_user.interested_topics.extend(interested_topics)

            # topics = Topic.query.filter(Topic.id.in_(interested_topics_ids)).all()
            # new_user.interested_topics = topics

        db.session.add(new_user)
        db.session.commit()

        return {"message": "User registered successfully"}, 201


def check_if_user_is_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        return False
    return user.role == 'admin'
