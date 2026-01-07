from flask import request, jsonify
from backend_app.services.cart_service import CartService


class CartController:

    @staticmethod
    def get_cart(current_user=None):
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-Id')

        cart = CartService.get_or_create_cart(
            user_id=current_user.id if current_user else None,
            session_id=session_id
        )

        response = jsonify(cart.to_dict())

        # Set session cookie for guest users
        if not current_user:
            response.set_cookie(
                'session_id',
                cart.session_id,
                max_age=30 * 24 * 60 * 60,  # 30 days
                httponly=True,
                samesite='Lax'
            )

        return response, 200

    @staticmethod
    def add_to_cart(current_user=None):
        data = request.get_json()

        if not data or 'product_id' not in data:
            return jsonify({'error': 'Product ID is required'}), 400

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

        response = jsonify({'message': message, 'cart': cart.to_dict()})

        # Set guest session cookie if needed
        if not current_user and cart.session_id:
            response.set_cookie(
                'session_id',
                cart.session_id,
                max_age=30 * 24 * 60 * 60,
                httponly=True,
                samesite='Lax'
            )

        return response, 200

    @staticmethod
    def update_cart_item(current_user, item_id):
        data = request.get_json()
        quantity = data.get('quantity')

        if quantity is None:
            return jsonify({'error': 'Quantity is required'}), 400

        cart, message = CartService.update_cart_item(item_id, quantity)
        if not cart:
            return jsonify({'error': message}), 400

        return jsonify({'message': message, 'cart': cart.to_dict()}), 200

    @staticmethod
    def remove_from_cart(current_user, item_id):
        cart, message = CartService.remove_from_cart(item_id)
        if not cart:
            return jsonify({'error': message}), 400

        return jsonify({'message': message, 'cart': cart.to_dict()}), 200

    @staticmethod
    def clear_cart(current_user):
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-Id')
        cart = None

        if current_user:
            cart, message = CartService.clear_cart(current_user.cart.id)
        elif session_id:
            guest_cart = CartService.get_cart_by_session_id(session_id)
            if guest_cart:
                cart, message = CartService.clear_cart(guest_cart.id)
            else:
                return jsonify({'error': 'Cart not found'}), 404
        else:
            return jsonify({'error': 'Cart not found'}), 404

        return jsonify({'message': message, 'cart': cart.to_dict() if cart else None}), 200

    @staticmethod
    def merge_carts(current_user):
        if not current_user:
            return jsonify({'error': 'Authentication required'}), 401

        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-Id')

        if not session_id:
            return jsonify({'message': 'No guest cart to merge'}), 200

        guest_cart = CartService.get_cart_by_session_id(session_id)
        if not guest_cart:
            return jsonify({'message': 'No guest cart to merge'}), 200

        cart, message = CartService.merge_carts(guest_cart.id, current_user.id)

        return jsonify({'message': message, 'cart': cart.to_dict() if cart else None}), 200
