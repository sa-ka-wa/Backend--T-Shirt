from flask import Blueprint, jsonify
from backend_app.controllers.order_controller import OrderController
from backend_app.utils.jwt_helper import token_required
from backend_app.utils.role_required import role_required
from backend_app.models.order import Order

order_bp = Blueprint('order', __name__)


# Get all orders - accessible by all authenticated users
@order_bp.route('/', methods=['GET'])
@token_required
def get_orders(current_user):
    return OrderController.get_orders(current_user)


# Search orders - accessible by all authenticated users
@order_bp.route('/search', methods=['GET'])
@token_required
def search_orders(current_user):
    return OrderController.search_orders(current_user)


# Get order statistics - accessible by all authenticated users
@order_bp.route('/stats', methods=['GET'])
@token_required
def get_order_stats(current_user):
    return OrderController.get_order_stats(current_user)


# Get specific order - accessible by all authenticated users
@order_bp.route('/<int:order_id>', methods=['GET'])
@token_required
def get_order(current_user, order_id):
    return OrderController.get_order(current_user, order_id)


# Create new order - only for customers
@order_bp.route('/', methods=['POST'])
@role_required('customer')
def create_order(current_user):
    return OrderController.create_order(current_user)


# Update order status - for staff and above
@order_bp.route('/<int:order_id>/status', methods=['PATCH'])
@role_required('super_admin', 'admin', 'brand_admin', 'brand_staff')
def update_order_status(current_user, order_id):
    return OrderController.update_order_status(current_user, order_id)


# Cancel order - for customers and staff
@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
@role_required('super_admin', 'admin', 'brand_admin', 'brand_staff', 'customer')
def cancel_order(current_user, order_id):
    return OrderController.cancel_order(current_user, order_id)


# Update shipping info - for staff and above
@order_bp.route('/<int:order_id>/shipping', methods=['PATCH'])
@role_required('super_admin', 'admin', 'brand_admin', 'brand_staff')
def update_shipping_info(current_user, order_id):
    return OrderController.update_shipping_info(current_user, order_id)


# Add tracking info - for staff and above
@order_bp.route('/<int:order_id>/tracking', methods=['POST'])
@role_required('super_admin', 'admin', 'brand_admin', 'brand_staff')
def add_tracking_info(current_user, order_id):
    return OrderController.add_tracking_info(current_user, order_id)


# Get order by number - for staff and above
@order_bp.route('/number/<string:order_number>', methods=['GET'])
@role_required('super_admin', 'admin', 'brand_admin', 'brand_staff')
def get_order_by_number(current_user, order_number):
    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    # Check permissions
    if current_user.role in ['brand_admin', 'brand_staff'] and order.user.brand_id != current_user.brand_id:
        return jsonify({'error': 'Unauthorized - can only view orders from your brand'}), 403

    return jsonify(order.to_dict(include_items=True, include_payments=True)), 200


# Track order (public endpoint)
@order_bp.route('/track/<string:tracking_number>', methods=['GET'])
def track_order(tracking_number):
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