from flask_restful import Resource
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
from api.app import db, mail
from api.app.models import AppointmentAvailability, User


class AppointmentAvailabilityGETResource(Resource):
    def get(self):
        return [availability.serialize() for availability in AppointmentAvailability.query.all()]


class AppointmentAvailabilityPOSTResource(Resource):
    def post(self):
        result = jwt_required()(self._post)()
        return result

    def _post(self):
        try:
            user_id = get_jwt_identity()
            availability = request.form.to_dict()

            new_availability = AppointmentAvailability(
                user_id=user_id,
                availability_time=availability["availability_time"]
            )
            new_availability.company_name = availability.get("company_name")
            new_availability.location = availability.get("location")
            new_availability.contact_information = availability.get(
                "contact_information")
            new_availability.bio = availability.get("bio")
            new_availability.specialty = availability.get("specialty")
            new_availability.experience_level = availability.get(
                "experience_level")

            db.session.add(new_availability)
            db.session.commit()
            return new_availability.serialize(), 201
        except Exception as e:
            print("Error: ", e)
            return {"message": "Invalid request"}, 400


class AppointmentAvailabilityResource(Resource):
    def get(self, id):
        availability = AppointmentAvailability.query.get(id)
        if availability:
            return availability.serialize()
        return None

    @jwt_required()
    def put(self, id):
        try:
            user_id = get_jwt_identity()
            availability = request.form

            availability = AppointmentAvailability.query.get(id)
            availability.availability_slot_start = availability.get(
                "availabilitySlotStart")
            availability.availability_slot_end = availability.get(
                "availabilitySlotEnd")
            availability.company_name = availability.get("company_name")
            availability.location = availability.get("location")
            availability.contact_information = availability.get(
                "contact_information")
            availability.bio = availability.get("bio")
            availability.specialty = availability.get("specialty")
            availability.experience_level = availability.get(
                "experience_level")

            db.session.commit()
            return availability.serialize(), 201
        except Exception as e:
            print("Error: ", e)
            return {"message": "Invalid request"}, 400

    @jwt_required()
    def delete(self, id):
        try:
            availability = AppointmentAvailability.query.get(id)
            db.session.delete(availability)
            db.session.commit()
            return {"message": "Availability deleted"}, 200
        except Exception as e:
            print("Error: ", e)
            return {"message": "Invalid request"}, 400


class AppointmentBookingResource(Resource):
    def get(self, id):
        availability = AppointmentAvailability.query.get(id)
        if availability:
            return availability.serialize()
        return None

    @jwt_required()
    def put(self, id):
        try:
            user_id = get_jwt_identity()
            availability = AppointmentAvailability.query.get(id)

            if availability.is_booked:
                return {"message": "Appointment not available"}, 400

            if availability.user_id == user_id:
                return {"message": "You can't book your own appointment"}, 400

            user = User.query.get(availability.user_id).first()
            if not user:
                return {"message": "User not found"}, 404

            booked_user = User.query.get(user_id).first()
            if not booked_user:
                return {"message": "User not found"}, 404

            availability.is_booked = True
            availability.booked_by = user_id
            db.session.commit()

            # Send email
            try:
                msg = Message(
                    "Appointment booked",
                    sender="j.ekhator@alustudent.com",
                    recipients=[user.email]
                )
                msg.body = f"Dear {user.username},\n\nYour appointment has been booked\n\nDate: {availability.availability_time}\n\nBooked by: {booked_user.username}\n\nBest regards,\nYour App Team"
                mail.send(msg)
            except Exception as e:
                print("Error: ", e)
                return {"message": "Failed to send email"}, 500

            return availability.serialize(), 200
        except Exception as e:
            print("Error: ", e)
            return {"message": "Invalid request"}, 400

    @jwt_required()
    def delete(self, id):
        try:
            availability = AppointmentAvailability.query.get(id)
            availability.is_booked = False
            availability.booked_by = None
            db.session.commit()
            return {"message": "Appointment cancelled"}, 200
        except Exception as e:
            print("Error: ", e)
            return {"message": "Invalid request"}, 400
