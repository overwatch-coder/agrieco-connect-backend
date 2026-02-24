from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.app import db
import os
import re
from api.app.cloudinary import upload_image

from api.app.models import Product, User

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'public/uploads/items_images'


def secure_filename(filename):
    filename = re.sub(r'[^A-Za-z0-9_.-]', '_', filename)
    return filename


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class ProductsGETResource(Resource):
    def get(self):
        return [product.serialize() for product in Product.query.all()]


class ProductsPOSTResource(Resource):
    def post(self):
        # Applying decorator directly and calling wrapped method
        result = jwt_required()(self._post)()
        return result

    def _post(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {"message": "Unauthorized"}, 401

        if 'image' not in request.files:
            return {"message": "No file part"}, 400

        image = request.files['image']
        if image.filename == '':
            return {"message": "No selected file"}, 400

        if image and allowed_file(image.filename):
            file_path = upload_image(image)
        else:
            return {"message": "File not allowed"}, 400

        data = request.form
        name = data.get('name')
        price = data.get('price')
        description = data.get('description')
        new_product = Product(
            name=name, price=price, description=description, image=file_path, user_id=user_id)
        db.session.add(new_product)
        db.session.commit()
        return new_product.serialize(), 201


class ProductResource(Resource):
    def get(self, id):
        product = Product.query.get(id)
        if product:
            return product.serialize()
        return None

    @jwt_required()
    def put(self, id):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {"message": "Unauthorized"}, 401
        data = request.get_json()
        name = data.get('name')
        price = data.get('price')
        description = data.get('description')
        image = data.get('image')

        product = Product.query.get(id)

        if product:
            product.name = name
            product.price = price
            product.description = description
            product.image = image

            db.session.commit()
            return product.serialize()
        return None

    @jwt_required()
    def delete(self, id):
        product = Product.query.get(id)
        if product:
            db.session.delete(product)
            db.session.commit()
            return product.serialize()
        return None
