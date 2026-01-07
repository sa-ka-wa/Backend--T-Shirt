from flask import Blueprint
from backend_app.controllers.cart_controller import CartController
from backend_app.utils.jwt_helper import cart_token_optional, token_required

cart_bp = Blueprint('cart', __name__)

# --------------------------------------
# Guest + Authenticated Users
# --------------------------------------

@cart_bp.route('', methods=['GET'])
@cart_token_optional
def get_cart(current_user):
    return CartController.get_cart(current_user)


@cart_bp.route('add', methods=['POST'])
@cart_token_optional
def add_to_cart(current_user):
    return CartController.add_to_cart(current_user)


@cart_bp.route('item/<int:item_id>', methods=['PUT'])
@cart_token_optional
def update_cart_item(current_user, item_id):
    return CartController.update_cart_item(current_user, item_id)


@cart_bp.route('item/<int:item_id>', methods=['DELETE'])
@cart_token_optional
def remove_from_cart(current_user, item_id):
    return CartController.remove_from_cart(current_user, item_id)


@cart_bp.route('clear', methods=['DELETE'])
@cart_token_optional
def clear_cart(current_user):
    return CartController.clear_cart(current_user)


# --------------------------------------
# Merge guest cart into authenticated cart
# --------------------------------------
@cart_bp.route('merge', methods=['POST'])
@token_required  # only logged-in users
def merge_carts(current_user):
    return CartController.merge_carts(current_user)
