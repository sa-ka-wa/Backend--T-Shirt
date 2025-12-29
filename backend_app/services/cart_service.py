# backend_app/services/cart_service.py
from backend_app.extensions import db
from backend_app.models.cart import Cart, CartItem
from backend_app.models.product import Product
import uuid


class CartService:
    @staticmethod
    def get_cart_by_user_id(user_id):
        return Cart.query.filter_by(user_id=user_id).first()

    @staticmethod
    def get_cart_by_session_id(session_id):
        return Cart.query.filter_by(session_id=session_id).first()

    @staticmethod
    def create_cart(user_id=None, session_id=None):
        cart = Cart(user_id=user_id, session_id=session_id)
        db.session.add(cart)
        db.session.commit()
        return cart

    @staticmethod
    def get_or_create_cart(user_id=None, session_id=None):
        if user_id:
            cart = CartService.get_cart_by_user_id(user_id)
        else:
            cart = CartService.get_cart_by_session_id(session_id)

        if not cart:
            cart = CartService.create_cart(user_id, session_id)

        return cart

    @staticmethod
    def add_to_cart(cart, product_id, quantity=1, size=None, color=None):
        product = Product.query.get(product_id)
        if not product:
            return None, 'Product not found'

        if product.stock_quantity < quantity:
            return None, f'Only {product.stock_quantity} items available'

        # Check if item already exists in cart
        existing_item = CartItem.query.filter_by(
            cart_id=cart.id,
            product_id=product_id,
            size=size,
            color=color
        ).first()

        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if new_quantity > product.stock_quantity:
                return None, f'Cannot add more than {product.stock_quantity} items'
            existing_item.quantity = new_quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                size=size,
                color=color
            )
            db.session.add(cart_item)

        db.session.commit()
        return cart, 'Item added to cart'

    @staticmethod
    def update_cart_item(item_id, quantity):
        cart_item = CartItem.query.get(item_id)
        if not cart_item:
            return None, 'Cart item not found'

        if quantity <= 0:
            db.session.delete(cart_item)
            db.session.commit()
            return cart_item.cart, 'Item removed from cart'

        if quantity > cart_item.product.stock_quantity:
            return None, f'Only {cart_item.product.stock_quantity} items available'

        cart_item.quantity = quantity
        db.session.commit()
        return cart_item.cart, 'Cart item updated'

    @staticmethod
    def remove_from_cart(item_id):
        cart_item = CartItem.query.get(item_id)
        if not cart_item:
            return None, 'Cart item not found'

        cart = cart_item.cart
        db.session.delete(cart_item)
        db.session.commit()
        return cart, 'Item removed from cart'

    @staticmethod
    def clear_cart(cart_id):
        cart = Cart.query.get(cart_id)
        if not cart:
            return None, 'Cart not found'

        CartItem.query.filter_by(cart_id=cart_id).delete()
        db.session.commit()
        return cart, 'Cart cleared'

    @staticmethod
    def merge_carts(guest_cart_id, user_id):
        guest_cart = Cart.query.get(guest_cart_id)
        if not guest_cart:
            return None, 'Guest cart not found'

        user_cart = CartService.get_cart_by_user_id(user_id)
        if not user_cart:
            user_cart = CartService.create_cart(user_id=user_id)

        for guest_item in guest_cart.items:
            existing_item = CartItem.query.filter_by(
                cart_id=user_cart.id,
                product_id=guest_item.product_id,
                size=guest_item.size,
                color=guest_item.color
            ).first()

            if existing_item:
                new_quantity = existing_item.quantity + guest_item.quantity
                if new_quantity <= guest_item.product.stock_quantity:
                    existing_item.quantity = new_quantity
                else:
                    existing_item.quantity = guest_item.product.stock_quantity
            else:
                guest_item.cart_id = user_cart.id

        db.session.delete(guest_cart)
        db.session.commit()
        return user_cart, 'Carts merged successfully'