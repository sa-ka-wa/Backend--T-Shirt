# backend_app/routes/cart_routes.py
from flask import Blueprint
from backend_app.controllers.cart_controller import CartController
from backend_app.utils.jwt_helper import token_required

cart_bp = Blueprint('cart', __name__)

# Public routes (guest users can use cart)
@cart_bp.route('/', methods=['GET'])
def get_cart():
    return CartController.get_cart()

@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    return CartController.add_to_cart()

@cart_bp.route('/item/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    return CartController.update_cart_item(item_id)

@cart_bp.route('/item/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    return CartController.remove_from_cart(item_id)

@cart_bp.route('/clear', methods=['DELETE'])
def clear_cart():
    return CartController.clear_cart()

# Protected routes (require login)
@cart_bp.route('/merge', methods=['POST'])
@token_required
def merge_carts():
    return CartController.merge_carts()