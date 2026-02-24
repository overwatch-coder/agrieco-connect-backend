from flask_restful import Resource
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Event, User
from app.cloudinary import upload_image
from datetime import datetime


def parse_datetime(date_str):
    # Adjust the format as needed. Here, assuming ISO 8601 format.
    return datetime.fromisoformat(date_str)


def parse_time(time_str):
    # Assuming time is in the format 'HH:MMAM/PM'
    return datetime.strptime(time_str, '%I:%M%p').strftime('%I:%M%p')


class EventsGETResource(Resource):
    def get(self):
        return [event.serialize() for event in Event.query.all()]


class EventsPOSTResource(Resource):
    def post(self):
        result = jwt_required()(self._post)()
        return result

    def _post(self):
        try:
            user_id = get_jwt_identity()
            event = request.form.to_dict()
            image = request.files.get('image')
            uploaded_image = None

            if image:
                try:
                    image = image.read()
                    uploaded_image = upload_image(image)
                except:
                    return {"message": "Invalid image"}, 400

            price = event.get("price") or 0

            start_date = parse_datetime(event["date"])
            start_time = parse_time(event["start_time"])
            end_time = parse_time(event["end_time"])

            new_event = Event(
                title=event["title"],
                description=event["description"],
                start_date=start_date,
                start_time=start_time,
                end_time=end_time,
                user_id=user_id,
                price=price,
                location=event["location"],
                image=uploaded_image
            )

            db.session.add(new_event)
            db.session.commit()
            return new_event.serialize(), 201

        except Exception as e:
            print("Error: ", e)
            return {"message": "Invalid request"}, 400


class EventResource(Resource):
    def get(self, id):
        event = Event.query.get(id)
        if event:
            return event.serialize()
        return None

    @jwt_required()
    def put(self, id):
        try:
            user_id = get_jwt_identity()
            event = request.form
            _event = Event.query.get(id)
            if _event:
                if _event.user_id != user_id:
                    return {"message": "You are not authorized to perform this action"}, 403
                _event.name = event["title"]
                _event.description = event["description"]
                _event.start_date = event["date"]
                _event.start_time = event["start_time"]
                _event.end_time = event["end_time"]
                _event.location = event["location"]
                image = request.files.get('image')
                if image:
                    try:
                        image = image.read()
                        uploaded_image = upload_image(image)
                        _event.image = uploaded_image
                    except:
                        return {"message": "Invalid image"}, 400
                db.session.commit()
                return _event.serialize(), 200
            return jsonify({"message": "Event could not be updated"}), 500
        except:
            return {"message": "Invalid request"}, 400

    @jwt_required()
    def delete(self, id):
        try:
            user_id = get_jwt_identity()
            event = Event.query.get(id)
            if event:
                if event.user_id != user_id:
                    return {"message": "You are not authorized to perform this action"}, 403
                db.session.delete(event)
                db.session.commit()
                return "", 204
            return jsonify({"message": "Event could not be deleted"}), 500
        except:
            return {"message": "Invalid request"}, 400


class EventGETAttendeesResource(Resource):
    def get(self, id):
        event = Event.query.get(id)
        if event:
            return [attendee.serialize() for attendee in event.attendees]
        return None


class EventPUTAttendeesResource(Resource):
    @jwt_required()
    def put(self, id):
        user_id = get_jwt_identity()
        event = Event.query.get(id)
        if event:
            if user_id:
                user = User.query.get(user_id)
                if not user:
                    return {"message": "User not found"}, 404

                if user in event.attendees:
                    event.attendees.remove(user)
                else:
                    event.attendees.append(user)
                db.session.commit()
                return {"message": "User added to event"}, 200
        return None
