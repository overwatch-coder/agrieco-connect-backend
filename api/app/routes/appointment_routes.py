from flask import Blueprint
from flask_restful import Api
from app.resources.appointment import AppointmentAvailabilityGETResource, AppointmentAvailabilityPOSTResource, AppointmentAvailabilityResource, AppointmentBookingResource

bp = Blueprint('appointment', __name__)
api = Api(bp)

api.add_resource(AppointmentAvailabilityGETResource, '/appointments')
api.add_resource(AppointmentAvailabilityPOSTResource, '/appointments')
api.add_resource(AppointmentAvailabilityResource, '/appointments/<int:id>')
api.add_resource(AppointmentBookingResource, '/appointments/<int:id>/bookings')