from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.order import Order, OrderItem
from backend_app.models.cart import Cart, CartItem
from backend_app.models.product import Product
from backend_app.services.order_service import OrderService
from backend_app.services.payment_service import PaymentService
from backend_app.utils.jwt_helper import get_current_user, get_current_user_id
from backend_app.utils.brand_filter import brand_filtered_query
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrderController:
    @staticmethod
    def get_orders():
        """Get all orders for current user or brand"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            # Get query parameters
            status = request.args.get('status')
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            search = request.args.get('search')

            # For regular users, only show their own orders
            if current_user.role == 'customer':
                result = OrderService.get_user_orders(current_user.id, limit, offset)
                return jsonify({
                    'orders': [order.to_dict(include_items=True) for order in result['orders']],
                    'total': result['total'],
                    'limit': result['limit'],
                    'offset': result['offset']
                }), 200

            # For brand admins, show brand orders
            elif current_user.role in ['brand_admin', 'brand_staff']:
                result = OrderService.get_all_orders(
                    brand_id=current_user.brand_id,
                    status=status,
                    limit=limit,
                    offset=offset
                )
                return jsonify({
                    'orders': [order.to_dict(include_items=True) for order in result['orders']],
                    'total': result['total'],
                    'limit': result['limit'],
                    'offset': result['offset']
                }), 200

            # For platform admins, show all orders
            elif current_user.role == 'admin':
                result = OrderService.get_all_orders(
                    status=status,
                    limit=limit,
                    offset=offset
                )
                return jsonify({
                    'orders': [order.to_dict(include_items=True) for order in result['orders']],
                    'total': result['total'],
                    'limit': result['limit'],
                    'offset': result['offset']
                }), 200

            else:
                return jsonify({'error': 'Unauthorized'}), 403

        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return jsonify({'error': 'Failed to get orders'}), 500

    @staticmethod
    def get_order(order_id):
        """Get specific order by ID"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            order = OrderService.get_order_by_id(order_id)
            if not order:
                return jsonify({'error': 'Order not found'}), 404

            # Check permissions
            if current_user.role == 'customer' and order.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403

            if current_user.role in ['brand_admin', 'brand_staff'] and order.user.brand_id != current_user.brand_id:
                return jsonify({'error': 'Unauthorized'}), 403

            return jsonify(order.to_dict(include_items=True, include_payments=True)), 200

        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            return jsonify({'error': 'Failed to get order'}), 500

    @staticmethod
    def create_order():
        """Create a new order"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return jsonify({'error': 'Unauthorized'}), 401

            data = request.get_json()

            # Validate required fields
            required_fields = ['shipping_address']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            # Check if creating from cart or direct items
            if 'items' in data:
                # Create direct order
                order = OrderService.create_direct_order(
                    user_id=current_user_id,
                    items_data=data['items'],
                    shipping_data=data['shipping_address'],
                    billing_data=data.get('billing_address'),
                    notes=data.get('notes', '')
                )
            else:
                # Create order from cart
                order = OrderService.create_order_from_cart(
                    user_id=current_user_id,
                    shipping_data=data['shipping_address'],
                    billing_data=data.get('billing_address'),
                    notes=data.get('notes', '')
                )

            return jsonify({
                'message': 'Order created successfully',
                'order': order.to_dict(include_items=True)
            }), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return jsonify({'error': 'Failed to create order'}), 500

    @staticmethod
    def update_order_status(order_id):
        """Update order status"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            data = request.get_json()
            if 'status' not in data:
                return jsonify({'error': 'Missing status field'}), 400

            order = OrderService.get_order_by_id(order_id)
            if not order:
                return jsonify({'error': 'Order not found'}), 404

            # Check permissions
            if current_user.role == 'customer' and order.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403

            # Only brand admins/staff or platform admins can update status
            if current_user.role not in ['brand_admin', 'brand_staff', 'admin']:
                return jsonify({'error': 'Insufficient permissions'}), 403

            if current_user.role in ['brand_admin', 'brand_staff'] and order.user.brand_id != current_user.brand_id:
                return jsonify({'error': 'Unauthorized'}), 403

            order = OrderService.update_order_status(
                order_id,
                data['status'],
                data.get('cancellation_reason')
            )

            return jsonify({
                'message': 'Order status updated successfully',
                'order': order.to_dict()
            }), 200

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return jsonify({'error': 'Failed to update order status'}), 500

    @staticmethod
    def cancel_order(order_id):
        """Cancel an order"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            data = request.get_json()

            order = OrderService.get_order_by_id(order_id)
            if not order:
                return jsonify({'error': 'Order not found'}), 404

            # Check permissions
            if current_user.role == 'customer' and order.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403

            if current_user.role in ['brand_admin', 'brand_staff'] and order.user.brand_id != current_user.brand_id:
                return jsonify({'error': 'Unauthorized'}), 403

            # Customers can only cancel pending orders
            if current_user.role == 'customer' and order.status != 'pending':
                return jsonify({'error': 'Only pending orders can be cancelled'}), 400

            order = OrderService.update_order_status(
                order_id,
                'cancelled',
                data.get('reason', 'Cancelled by user')
            )

            return jsonify({
                'message': 'Order cancelled successfully',
                'order': order.to_dict()
            }), 200

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return jsonify({'error': 'Failed to cancel order'}), 500

    @staticmethod
    def update_shipping_info(order_id):
        """Update shipping information"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            data = request.get_json()
            if 'shipping_info' not in data:
                return jsonify({'error': 'Missing shipping_info field'}), 400

            order = OrderService.get_order_by_id(order_id)
            if not order:
                return jsonify({'error': 'Order not found'}), 404

            # Check permissions
            if current_user.role == 'customer' and order.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403

            if current_user.role in ['brand_admin', 'brand_staff'] and order.user.brand_id != current_user.brand_id:
                return jsonify({'error': 'Unauthorized'}), 403

            # Only pending orders can have shipping info updated
            if order.status != 'pending':
                return jsonify({'error': 'Shipping info can only be updated for pending orders'}), 400

            order = OrderService.update_shipping_info(order_id, data['shipping_info'])

            return jsonify({
                'message': 'Shipping information updated successfully',
                'order': order.to_dict()
            }), 200

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error updating shipping info: {str(e)}")
            return jsonify({'error': 'Failed to update shipping info'}), 500

    @staticmethod
    def add_tracking_info(order_id):
        """Add tracking information"""
        try:
            current_user = get_current_user()
            if not current_user or current_user.role not in ['brand_admin', 'brand_staff', 'admin']:
                return jsonify({'error': 'Unauthorized'}), 401

            data = request.get_json()
            required_fields = ['tracking_number', 'carrier']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            order = OrderService.get_order_by_id(order_id)
            if not order:
                return jsonify({'error': 'Order not found'}), 404

            # Check brand permissions
            if current_user.role in ['brand_admin', 'brand_staff'] and order.user.brand_id != current_user.brand_id:
                return jsonify({'error': 'Unauthorized'}), 403

            order = OrderService.add_tracking_info(
                order_id,
                data['tracking_number'],
                data['carrier'],
                datetime.fromisoformat(data['estimated_delivery']) if 'estimated_delivery' in data else None
            )

            return jsonify({
                'message': 'Tracking information added successfully',
                'order': order.to_dict()
            }), 200

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error adding tracking info: {str(e)}")
            return jsonify({'error': 'Failed to add tracking info'}), 500

    @staticmethod
    def get_order_stats():
        """Get order statistics"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            # Get query parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            if start_date:
                start_date = datetime.fromisoformat(start_date)
            if end_date:
                end_date = datetime.fromisoformat(end_date)

            brand_id = current_user.brand_id if current_user.role in ['brand_admin', 'brand_staff'] else None
            user_id = current_user.id if current_user.role == 'customer' else None

            stats = OrderService.calculate_order_stats(
                user_id=user_id,
                brand_id=brand_id,
                start_date=start_date,
                end_date=end_date
            )

            return jsonify(stats), 200

        except Exception as e:
            logger.error(f"Error getting order stats: {str(e)}")
            return jsonify({'error': 'Failed to get order statistics'}), 500

    @staticmethod
    def search_orders():
        """Search orders"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            search_term = request.args.get('q')
            if not search_term:
                return jsonify({'error': 'Missing search term'}), 400

            brand_id = current_user.brand_id if current_user.role in ['brand_admin', 'brand_staff'] else None
            user_id = current_user.id if current_user.role == 'customer' else None

            orders = OrderService.search_orders(search_term, user_id=user_id, brand_id=brand_id)

            return jsonify({
                'orders': [order.to_dict(include_items=True) for order in orders],
                'total': len(orders)
            }), 200

        except Exception as e:
            logger.error(f"Error searching orders: {str(e)}")
            return jsonify({'error': 'Failed to search orders'}), 500