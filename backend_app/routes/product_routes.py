# backend_app/routes/product_routes.py
from flask import Blueprint
from backend_app.controllers.product_controller import ProductController
from backend_app.utils.jwt_helper import token_required, admin_required
from backend_app.utils.role_required import role_required

product_bp = Blueprint('product', __name__)

@product_bp.route('/', methods=['GET'])
def get_all_products():
    return ProductController.get_all_products()

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    return ProductController.get_product(product_id)

@product_bp.route('/', methods=['POST'])
@token_required
# @admin_required
@role_required('admin', 'super_admin')
def create_product(current_user):
    return ProductController.create_product(current_user)

@product_bp.route('/<int:product_id>', methods=['PUT'])
@token_required
# @admin_required
@role_required('admin', 'super_admin')
def update_product(current_user, product_id):
    return ProductController.update_product(current_user, product_id)

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
# @admin_required
@role_required('admin', 'super_admin')
def delete_product(current_user, product_id):
    return ProductController.delete_product(current_user,product_id)

@product_bp.route('/<int:product_id>/stock', methods=['PUT'])
@token_required
# @admin_required
@role_required('admin', 'super_admin')
def update_stock(current_user, product_id):
    return ProductController.update_stock(current_user,product_id)