from flask import Blueprint
from backend_app.controllers.order_controller import OrderController
from backend_app.utils.jwt_helper import token_required

order_bp = Blueprint('order', __name__)


# Get all orders
@order_bp.route('/', methods=['GET'])
@token_required
def get_orders():
    return OrderController.get_orders()


# Search orders
@order_bp.route('/search', methods=['GET'])
@token_required
def search_orders():
    return OrderController.search_orders()


# Get order statistics
@order_bp.route('/stats', methods=['GET'])
@token_required
def get_order_stats():
    return OrderController.get_order_stats()


# Get specific order
@order_bp.route('/<int:order_id>', methods=['GET'])
@token_required
def get_order(order_id):
    return OrderController.get_order(order_id)


# Create new order
@order_bp.route('/', methods=['POST'])
@token_required
def create_order():
    return OrderController.create_order()


# Update order status
@order_bp.route('/<int:order_id>/status', methods=['PATCH'])
@token_required
def update_order_status(order_id):
    return OrderController.update_order_status(order_id)


# Cancel order
@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
@token_required
def cancel_order(order_id):
    return OrderController.cancel_order(order_id)


# Update shipping info
@order_bp.route('/<int:order_id>/shipping', methods=['PATCH'])
@token_required
def update_shipping_info(order_id):
    return OrderController.update_shipping_info(order_id)


# Add tracking info
@order_bp.route('/<int:order_id>/tracking', methods=['POST'])
@token_required
def add_tracking_info(order_id):
    return OrderController.add_tracking_info(order_id)


# Get order by number
@order_bp.route('/number/<string:order_number>', methods=['GET'])
@token_required
def get_order_by_number(order_number):
    from backend_app.models.order import Order
    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify(order.to_dict(include_items=True, include_payments=True)), 200


# Track order (public endpoint)
@order_bp.route('/track/<string:tracking_number>', methods=['GET'])
def track_order(tracking_number):
    from backend_app.models.order import Order
    from flask import jsonify

    order = Order.query.filter_by(tracking_number=tracking_number).first()
    if not order:
        return jsonify({'error': 'Tracking number not found'}), 404

    # Return minimal info for public tracking
    return jsonify({
        'order_number': order.order_number,
        'status': order.status,
        'tracking_number': order.tracking_number,
        'carrier': order.carrier,
        'estimated_delivery': order.estimated_delivery.isoformat() if order.estimated_delivery else None,
        'shipping_address': {
            'city': order.shipping_address.get('city', ''),
            'country': order.shipping_address.get('country', '')
        }
    }), 200