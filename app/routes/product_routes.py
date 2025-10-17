# app/routes/product_routes.py
from flask import Blueprint
from app.controllers.product_controller import ProductController
from app.utils.jwt_helper import token_required, admin_required

product_bp = Blueprint('product', __name__)

@product_bp.route('/', methods=['GET'])
def get_all_products():
    return ProductController.get_all_products()

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    return ProductController.get_product(product_id)

@product_bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_product(current_user):
    return ProductController.create_product()

@product_bp.route('/<int:product_id>', methods=['PUT'])
@token_required
@admin_required
def update_product(current_user, product_id):
    return ProductController.update_product(product_id)

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_product(current_user, product_id):
    return ProductController.delete_product(product_id)

@product_bp.route('/<int:product_id>/stock', methods=['PUT'])
@token_required
@admin_required
def update_stock(current_user, product_id):
    return ProductController.update_stock(product_id)