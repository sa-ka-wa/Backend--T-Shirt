# app/routes/brand_routes.py
from flask import Blueprint
from app.controllers.brand_controller import BrandController
from app.utils.jwt_helper import token_required, admin_required

brand_bp = Blueprint('brand', __name__)

@brand_bp.route('/', methods=['GET'])
def get_all_brands():
    return BrandController.get_all_brands()

@brand_bp.route('/<int:brand_id>', methods=['GET'])
def get_brand(brand_id):
    return BrandController.get_brand(brand_id)

@brand_bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_brand(current_user):
    return BrandController.create_brand()

@brand_bp.route('/<int:brand_id>', methods=['PUT'])
@token_required
@admin_required
def update_brand(current_user, brand_id):
    return BrandController.update_brand(brand_id)

@brand_bp.route('/<int:brand_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_brand(current_user, brand_id):
    return BrandController.delete_brand(brand_id)

@brand_bp.route('/<int:brand_id>/tshirts', methods=['GET'])
def get_brand_tshirts(brand_id):
    return BrandController.get_brand_tshirts(brand_id)