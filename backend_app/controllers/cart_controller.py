# backend_app/controllers/cart_controller.py
from flask import request, jsonify
from backend_app.services.cart_service import CartService
from backend_app.utils.jwt_helper import get_current_user
import uuid


class CartController:
    @staticmethod
    def get_cart():
        current_user = get_current_user()
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-Id')

        if current_user:
            cart = CartService.get_or_create_cart(user_id=current_user.id)
        elif session_id:
            cart = CartService.get_or_create_cart(session_id=session_id)
        else:
            session_id = str(uuid.uuid4())
            cart = CartService.get_or_create_cart(session_id=session_id)

        response = jsonify(cart.to_dict())

        # Set session cookie for guest users
        if not current_user:
            response.set_cookie('session_id', cart.session_id, max_age=30 * 24 * 60 * 60)  # 30 days

        return response, 200

    @staticmethod
    def add_to_cart():
        data = request.get_json()

        if not data or 'product_id' not in data:
            return jsonify({'error': 'Product ID is required'}), 400

        current_user = get_current_user()
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-Id')

        cart = CartService.get_or_create_cart(
            user_id=current_user.id if current_user else None,
            session_id=session_id
        )

        cart, message = CartService.add_to_cart(
            cart,
            data['product_id'],
            data.get('quantity', 1),
            data.get('size'),
            data.get('color')
        )

        if not cart:
            return jsonify({'error': message}), 400

        return jsonify({
            'message': message,
            'cart': cart.to_dict()
        }), 200

    @staticmethod
    def update_cart_item(item_id):
        data = request.get_json()

        if 'quantity' not in data:
            return jsonify({'error': 'Quantity is required'}), 400

        cart, message = CartService.update_cart_item(item_id, data['quantity'])

        if not cart:
            return jsonify({'error': message}), 404

        return jsonify({
            'message': message,
            'cart': cart.to_dict()
        }), 200

    @staticmethod
    def remove_from_cart(item_id):
        cart, message = CartService.remove_from_cart(item_id)

        if not cart:
            return jsonify({'error': message}), 404

        return jsonify({
            'message': message,
            'cart': cart.to_dict()
        }), 200

    @staticmethod
    def clear_cart():
        current_user = get_current_user()
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-Id')

        if current_user:
            cart = CartService.get_cart_by_user_id(current_user.id)
        else:
            cart = CartService.get_cart_by_session_id(session_id)

        if not cart:
            return jsonify({'error': 'Cart not found'}), 404

        cart, message = CartService.clear_cart(cart.id)
        return jsonify({'message': message}), 200

    @staticmethod
    def merge_carts():
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not authenticated'}), 401

        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-Id')
        if not session_id:
            return jsonify({'message': 'No guest cart to merge'}), 200

        guest_cart = CartService.get_cart_by_session_id(session_id)
        if not guest_cart:
            return jsonify({'message': 'No guest cart to merge'}), 200

        cart, message = CartService.merge_carts(guest_cart.id, current_user.id)

        return jsonify({
            'message': message,
            'cart': cart.to_dict() if cart else None
        }), 200