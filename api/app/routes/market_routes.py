from flask import Blueprint
from flask_restful import Api
from app.resources.market import ProductsGETResource, ProductResource, ProductsPOSTResource

bp = Blueprint('market', __name__)
api = Api(bp)

api.add_resource(ProductsGETResource, '/marketplaces/items')
api.add_resource(ProductResource, '/marketplaces/items', '/marketplaces/items/<int:id>')
api.add_resource(ProductsPOSTResource, '/marketplaces/items')