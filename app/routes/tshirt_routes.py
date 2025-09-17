from flask import Blueprint
from app.controllers.tshirt_controller import TShirtController
from app.utils.jwt_helper import token_required, admin_required

tshirt_bp = Blueprint('tshirt', __name__)

@tshirt_bp.route('/', methods=['GET'])
def get_all_tshirts():
    return TShirtController.get_all_tshirts()

@tshirt_bp.route('/<int:tshirt_id>', methods=['GET'])
def get_tshirt(tshirt_id):
    return TShirtController.get_tshirt(tshirt_id)

@tshirt_bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_tshirt(current_user):
    return TShirtController.create_tshirt()

@tshirt_bp.route('/<int:tshirt_id>', methods=['PUT'])
@token_required
@admin_required
def update_tshirt(current_user, tshirt_id):
    return TShirtController.update_tshirt(tshirt_id)

@tshirt_bp.route('/<int:tshirt_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_tshirt(current_user, tshirt_id):
    return TShirtController.delete_tshirt(tshirt_id)