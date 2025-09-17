from flask import Blueprint
from app.controllers.order_controller import OrderController
from app.utils.jwt_helper import token_required

order_bp = Blueprint('order', __name__)

@order_bp.route('/', methods=['GET'])
@token_required
def get_orders():
    return OrderController.get_orders()

@order_bp.route('/<int:order_id>', methods=['GET'])
@token_required
def get_order(order_id):
    return OrderController.get_order(order_id)

@order_bp.route('/', methods=['POST'])
@token_required
def create_order():
    return OrderController.create_order()

@order_bp.route('/<int:order_id>', methods=['PUT'])
@token_required
def update_order(order_id):
    return OrderController.update_order(order_id)