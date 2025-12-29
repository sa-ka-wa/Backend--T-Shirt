# backend_app/routes/brand_routes.py
from flask import Blueprint
from backend_app.controllers.brand_controller import BrandController
from backend_app.utils.jwt_helper import token_required, admin_required
from backend_app.utils.role_required import role_required

brand_bp = Blueprint('brand', __name__)

@brand_bp.route('', methods=['GET'])
def get_all_brands():
    return BrandController.get_all_brands()

@brand_bp.route('/<int:brand_id>', methods=['GET'])
def get_brand(brand_id):
    return BrandController.get_brand(brand_id)

@brand_bp.route('/', methods=['POST'])
# @token_required
# @admin_required
@role_required('super_admin')
def create_brand(current_user):
    return BrandController.create_brand(current_user)

@brand_bp.route('/<int:brand_id>', methods=['PUT'])
# @token_required
# @admin_required
@role_required('super_admin')
def update_brand(current_user, brand_id):
    return BrandController.update_brand(current_user,brand_id)

@brand_bp.route('/<int:brand_id>', methods=['DELETE'])
# @token_required
# @admin_required
@role_required('super_admin')
def delete_brand(current_user, brand_id):
    return BrandController.delete_brand(current_user,brand_id)

@brand_bp.route('/<int:brand_id>/tshirts', methods=['GET'])
def get_brand_tshirts(brand_id):
    return BrandController.get_brand_tshirts(brand_id)

@brand_bp.route("/by-subdomain", methods=["GET"])
def get_brand_by_subdomain():
    return BrandController.get_brand_by_subdomain()
@brand_bp.route("/update-subdomain", methods=["POST"])
def update_subdomain():
    return BrandController.update_subdomain()
