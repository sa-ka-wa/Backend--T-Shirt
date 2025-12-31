from backend_app.extensions import db
from backend_app.models.payment import Payment
from backend_app.models.order import Order
from backend_app.models.user import User
from datetime import datetime
import requests
import json
import base64
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    def get_all_payments(user_id=None, order_id=None, status=None, limit=50, offset=0):
        """Get all payments with optional filters"""
        query = Payment.query

        if user_id:
            query = query.filter_by(user_id=user_id)

        if order_id:
            query = query.filter_by(order_id=order_id)

        if status:
            query = query.filter_by(status=status)

        total = query.count()
        payments = query.order_by(Payment.initiated_at.desc()).limit(limit).offset(offset).all()

        return {
            'payments': payments,
            'total': total,
            'limit': limit,
            'offset': offset
        }

    @staticmethod
    def get_payment_by_id(payment_id):
        """Get payment by ID"""
        return Payment.query.get(payment_id)

    @staticmethod
    def get_payment_by_reference(payment_reference):
        """Get payment by reference number"""
        return Payment.query.filter_by(payment_reference=payment_reference).first()

    @staticmethod
    def create_payment(order_id, amount, payment_method, phone_number=None, metadata=None):
        """Create a new payment record"""
        try:
            order = Order.query.get(order_id)
            if not order:
                raise ValueError("Order not found")

            if order.status == 'cancelled':
                raise ValueError("Cannot create payment for cancelled order")

            payment = Payment(
                user_id=order.user_id,
                order_id=order_id,
                amount=amount,
                payment_method=payment_method,
                status='pending',
                metadata=metadata or {}
            )

            if payment_method == 'mpesa' and phone_number:
                payment.phone_number = phone_number
                payment.provider = 'safaricom'

            db.session.add(payment)
            db.session.commit()

            return payment

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating payment: {str(e)}")
            raise

    @staticmethod
    def update_payment_status(payment_id, status, transaction_data=None):
        """Update payment status"""
        payment = Payment.query.get(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        payment.status = status

        if status == 'completed':
            payment.completed_at = datetime.utcnow()

            # Update order status
            order = Order.query.get(payment.order_id)
            if order:
                order.status = 'processing'
                order.updated_at = datetime.utcnow()

        elif status == 'failed':
            payment.failed_at = datetime.utcnow()

        if transaction_data:
            if 'transaction_id' in transaction_data:
                payment.transaction_id = transaction_data['transaction_id']
            if 'mpesa_receipt_number' in transaction_data:
                payment.mpesa_receipt_number = transaction_data['mpesa_receipt_number']
            if 'result_code' in transaction_data:
                payment.result_code = transaction_data['result_code']
            if 'result_description' in transaction_data:
                payment.result_description = transaction_data['result_description']

        db.session.commit()
        return payment

    @staticmethod
    def process_refund(payment_id, refund_amount, refund_reason):
        """Process payment refund"""
        payment = Payment.query.get(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status != 'completed':
            raise ValueError("Can only refund completed payments")

        if refund_amount > payment.amount:
            raise ValueError("Refund amount cannot exceed original payment")

        payment.refund_amount = refund_amount
        payment.refund_reason = refund_reason

        # Update order status if full refund
        if refund_amount == payment.amount:
            order = Order.query.get(payment.order_id)
            if order:
                order.status = 'refunded'

        db.session.commit()
        return payment

    @staticmethod
    def get_payment_stats(user_id=None, brand_id=None):
        """Calculate payment statistics"""
        query = Payment.query

        if user_id:
            query = query.filter_by(user_id=user_id)

        if brand_id:
            query = query.join(Order).join(User).filter(User.brand_id == brand_id)

        total_payments = query.count()
        total_amount = db.session.query(db.func.sum(Payment.amount)).scalar() or 0

        status_counts = {}
        for status in ['pending', 'completed', 'failed', 'refunded']:
            count = query.filter_by(status=status).count()
            status_counts[status] = count

        method_counts = {}
        for method in ['mpesa', 'card', 'bank_transfer']:
            count = query.filter_by(payment_method=method).count()
            method_counts[method] = count

        return {
            'total_payments': total_payments,
            'total_amount': total_amount,
            'status_counts': status_counts,
            'method_counts': method_counts
        }