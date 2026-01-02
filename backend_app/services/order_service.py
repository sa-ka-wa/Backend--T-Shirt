from backend_app.extensions import db
from backend_app.models.order import Order, OrderItem
from backend_app.models.cart import Cart, CartItem
from backend_app.models.product import Product
from backend_app.models.user import User
from backend_app.models.payment import Payment
from datetime import datetime
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    def get_all_orders(user_id=None, brand_id=None, status=None, limit=50, offset=0):
        """Get all orders with optional filters"""
        query = Order.query

        if user_id:
            query = query.filter_by(user_id=user_id)

        if brand_id:
            query = query.join(User).filter(User.brand_id == brand_id)

        if status:
            query = query.filter_by(status=status)

        total = query.count()
        orders = query.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()

        return {
            'orders': orders,
            'total': total,
            'limit': limit,
            'offset': offset
        }

    @staticmethod
    def get_order_by_id(order_id):
        """Get order by ID"""
        return Order.query.get(order_id)

    @staticmethod
    def get_order_by_number(order_number):
        """Get order by order number"""
        return Order.query.filter_by(order_number=order_number).first()

    @staticmethod
    def create_order_from_cart(user_id, shipping_data, billing_data=None, notes=""):
        """Create order from user's cart"""
        try:
            cart = Cart.query.filter_by(user_id=user_id).first()
            if not cart or not cart.items:
                raise ValueError("Cart is empty")

            # Calculate totals
            subtotal = sum(item.product.price * item.quantity for item in cart.items)
            shipping_amount = 200  # Fixed shipping for Kenya
            tax_amount = subtotal * 0.16  # 16% VAT
            total_amount = subtotal + shipping_amount + tax_amount

            # Create order
            order = Order(
                user_id=user_id,
                subtotal=subtotal,
                shipping_amount=shipping_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                shipping_address=shipping_data,
                billing_address=billing_data or shipping_data,
                notes=notes
            )

            # Create order items from cart items
            for cart_item in cart.items:
                if cart_item.product.stock_quantity < cart_item.quantity:
                    raise ValueError(f"Insufficient stock for {cart_item.product.title}")

                order_item = OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product.price,
                    total_price=cart_item.product.price * cart_item.quantity,
                    size=cart_item.size,
                    color=cart_item.color,
                    customization_data=cart_item.customization_data if hasattr(cart_item,
                                                                               'customization_data') else None
                )
                order.items.append(order_item)

                # Update product stock
                cart_item.product.stock_quantity -= cart_item.quantity

            db.session.add(order)

            # Clear cart after successful order
            cart.items = []

            db.session.commit()

            return order

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating order: {str(e)}")
            raise

    @staticmethod
    def create_direct_order(user_id, items_data, shipping_data, billing_data=None, notes=""):
        """Create order directly (for custom designs or API)"""
        try:
            subtotal = 0
            order_items = []

            # Validate items and calculate totals
            for item_data in items_data:
                product = Product.query.get(item_data['product_id'])
                if not product:
                    raise ValueError(f"Product not found: {item_data['product_id']}")

                if product.stock_quantity < item_data.get('quantity', 1):
                    raise ValueError(f"Insufficient stock for {product.title}")

                quantity = item_data.get('quantity', 1)
                subtotal += product.price * quantity

                order_items.append({
                    'product': product,
                    'quantity': quantity,
                    'size': item_data.get('size'),
                    'color': item_data.get('color'),
                    'customization_data': item_data.get('customization_data'),
                    'unit_price': product.price
                })

            shipping_amount = 200
            tax_amount = subtotal * 0.16
            total_amount = subtotal + shipping_amount + tax_amount

            # Create order
            order = Order(
                user_id=user_id,
                subtotal=subtotal,
                shipping_amount=shipping_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                shipping_address=shipping_data,
                billing_address=billing_data or shipping_data,
                notes=notes
            )

            # Add order items
            for item_data in order_items:
                order_item = OrderItem(
                    product_id=item_data['product'].id,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['unit_price'] * item_data['quantity'],
                    size=item_data['size'],
                    color=item_data['color'],
                    customization_data=item_data['customization_data']
                )
                order.items.append(order_item)

                # Update stock
                item_data['product'].stock_quantity -= item_data['quantity']

            db.session.add(order)
            db.session.commit()

            return order

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating direct order: {str(e)}")
            raise

    @staticmethod
    def update_order_status(order_id, status, cancellation_reason=None):
        """Update order status"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")

        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        order.status = status
        order.updated_at = datetime.utcnow()

        if status == 'cancelled':
            order.cancelled_at = datetime.utcnow()
            order.cancellation_reason = cancellation_reason

            # Restore stock for cancelled orders
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock_quantity += item.quantity

        elif status == 'delivered':
            order.delivered_at = datetime.utcnow()

        db.session.commit()
        return order

    @staticmethod
    def update_shipping_info(order_id, shipping_info):
        """Update shipping information"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")

        order.shipping_address = shipping_info
        order.updated_at = datetime.utcnow()
        db.session.commit()
        return order

    @staticmethod
    def add_tracking_info(order_id, tracking_number, carrier, estimated_delivery=None):
        """Add tracking information to order"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")

        order.tracking_number = tracking_number
        order.carrier = carrier
        order.status = 'shipped'
        order.updated_at = datetime.utcnow()

        if estimated_delivery:
            order.estimated_delivery = estimated_delivery

        db.session.commit()
        return order

    @staticmethod
    def get_user_orders(user_id, limit=50, offset=0):
        """Get orders for a specific user"""
        query = Order.query.filter_by(user_id=user_id)
        total = query.count()
        orders = query.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()

        return {
            'orders': orders,
            'total': total,
            'limit': limit,
            'offset': offset
        }

    @staticmethod
    def calculate_order_stats(user_id=None, brand_id=None, start_date=None, end_date=None):
        """Calculate order statistics"""
        query = Order.query

        if user_id:
            query = query.filter_by(user_id=user_id)

        if brand_id:
            query = query.join(User).filter(User.brand_id == brand_id)

        if start_date:
            query = query.filter(Order.created_at >= start_date)

        if end_date:
            query = query.filter(Order.created_at <= end_date)

        total_orders = query.count()
        total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0

        status_counts = {}
        for status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            count = query.filter_by(status=status).count()
            status_counts[status] = count

        # Calculate average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        return {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'average_order_value': avg_order_value,
            'status_counts': status_counts
        }

    @staticmethod
    def search_orders(search_term, user_id=None, brand_id=None):
        """Search orders by order number, customer name, or email"""
        query = Order.query

        if user_id:
            query = query.filter_by(user_id=user_id)

        if brand_id:
            query = query.join(User).filter(User.brand_id == brand_id)

        # Search by order number
        orders_by_number = query.filter(Order.order_number.ilike(f'%{search_term}%')).all()

        # Search by user name or email
        orders_by_user = query.join(User).filter(
            (User.name.ilike(f'%{search_term}%')) |
            (User.email.ilike(f'%{search_term}%'))
        ).all()

        # Combine and remove duplicates
        all_orders = list({order.id: order for order in orders_by_number + orders_by_user}.values())

        return all_orders