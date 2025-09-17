from flask import request, jsonify
from app.extensions import db
from app.models.order import Order
from app.services.order_service import OrderService


class OrderController:
    @staticmethod
    def get_orders():
        orders = OrderService.get_all_orders()
        return jsonify([order.to_dict() for order in orders])

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
        required_fields = ['user_id', 'tshirt_id', 'quantity', 'shipping_address']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        order = OrderService.create_order(
            data['user_id'],
            data['tshirt_id'],
            data['quantity'],
            data['shipping_address']
        )

        return jsonify(order.to_dict()), 201

    @staticmethod
    def update_order(order_id):
        data = request.get_json()
        order = OrderService.update_order(order_id, data)

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        return jsonify(order.to_dict())