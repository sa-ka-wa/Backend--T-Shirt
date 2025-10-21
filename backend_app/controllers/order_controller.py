from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.order import Order
from backend_app.services.order_service import OrderService
from backend_app.models.user import User
from backend_app.utils.jwt_helper import get_current_user
from backend_app.utils.brand_filter import brand_filtered_query


class OrderController:
    @staticmethod
    def get_orders():
        orders = brand_filtered_query(Order).all()
        return jsonify([order.to_dict() for order in orders]), 200

    @staticmethod
    def get_order(order_id):
        order = OrderService.get_order_by_id(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        return jsonify(order.to_dict())

    @staticmethod
    def create_order():
        data = request.get_json()

        # Validate required fields
        required_fields = ['user_id', 'product_id', 'quantity', 'shipping_address']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        order = OrderService.create_order(
            data['user_id'],
            data['product_id'],
            data['quantity'],
            data['shipping_address']
        )
        if not order:
            return jsonify({'error': 'Invalid product ID'}), 400


        return jsonify(order.to_dict()), 201

    @staticmethod
    def update_order(order_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing update data'}), 400

        order = OrderService.update_order(order_id, data)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        return jsonify(order.to_dict()), 200