# jwt_errors.py

from flask import jsonify
from flask_jwt_extended import JWTManager

jwt = JWTManager()

@jwt.expired_token_loader
def expired_token_callback():
    return jsonify({
        'message': 'Token has expired',
        'error': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'message': 'Signature verification failed',
        'error': 'invalid_token'
    }), 401

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({
        'message': 'Missing Authorization Header',
        'error': 'authorization_required'
    }), 401

@jwt.needs_fresh_token_loader
def token_not_fresh_callback():
    return jsonify({
        'message': 'Fresh token required',
        'error': 'fresh_token_required'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback():
    return jsonify({
        'message': 'Token has been revoked',
        'error': 'token_revoked'
    }), 401
