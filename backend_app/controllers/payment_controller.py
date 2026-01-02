from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.payment import Payment
from backend_app.models.order import Order
from backend_app.services.payment_service import PaymentService
from backend_app.utils.jwt_helper import get_current_user, get_current_user_id
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class PaymentController:
    @staticmethod
    def get_payments(current_user):
        """Get all payments for current user"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            # Get query parameters
            status = request.args.get('status')
            order_id = request.args.get('order_id')
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)

            payment_service = PaymentService()

            if current_user.role == 'customer':
                result = payment_service.get_user_payments(
                    user_id=current_user.id,
                    status=status,
                    limit=limit,
                    offset=offset
                )
            else:
                # For admins, get all payments
                # Note: You might want to add admin-specific logic here
                result = payment_service.get_user_payments(
                    user_id=current_user.id,
                    status=status,
                    limit=limit,
                    offset=offset
                )

            payments_data = [payment.to_dict() for payment in result['payments']]

            return jsonify({
                'payments': payments_data,
                'total': result['total'],
                'limit': result['limit'],
                'offset': result['offset']
            }), 200

        except Exception as e:
            logger.error(f"Error getting payments: {str(e)}")
            return jsonify({'error': 'Failed to get payments'}), 500

    @staticmethod
    def get_payment(current_user,payment_id):
        """Get specific payment"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            payment_service = PaymentService()
            payment = payment_service.get_payment_by_id(payment_id)

            if not payment:
                return jsonify({'error': 'Payment not found'}), 404

            # Check if user owns the payment or is admin
            if payment.user_id != current_user.id and current_user.role not in ['admin', 'brand_admin']:
                return jsonify({'error': 'Unauthorized'}), 403

            return jsonify(payment.to_dict()), 200

        except Exception as e:
            logger.error(f"Error getting payment: {str(e)}")
            return jsonify({'error': 'Failed to get payment'}), 500

    @staticmethod
    def initiate_payment(current_user):
        """Initiate a payment for an order"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            data = request.get_json()

            # Validate required fields
            required_fields = ['order_id', 'payment_method', 'amount']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            # Get order
            order = Order.query.get(data['order_id'])
            if not order:
                return jsonify({'error': 'Order not found'}), 404

            # Check if user owns the order
            if order.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403

            # Validate amount
            if float(data['amount']) != float(order.total_amount):
                return jsonify({'error': 'Payment amount must match order total'}), 400

            payment_service = PaymentService()

            # Create payment
            payment = payment_service.create_payment(
                order_id=data['order_id'],
                amount=data['amount'],
                payment_method=data['payment_method'],
                phone_number=data.get('phone_number'),
                metadata=data.get('metadata', {})
            )

            # If M-Pesa, initiate STK Push
            if data['payment_method'] == 'mpesa' and 'phone_number' in data:
                try:
                    stk_response = payment_service.initiate_stk_push(
                        phone_number=data['phone_number'],
                        amount=data['amount'],
                        order_id=data['order_id'],
                        description=f"Payment for order #{order.order_number}"
                    )

                    return jsonify({
                        'message': 'M-Pesa payment initiated',
                        'payment': payment.to_dict(),
                        'stk_push': stk_response
                    }), 201
                except Exception as stk_error:
                    logger.error(f"STK Push failed: {str(stk_error)}")
                    return jsonify({
                        'error': f'Failed to initiate M-Pesa payment: {str(stk_error)}',
                        'payment': payment.to_dict()
                    }), 400

            return jsonify({
                'message': 'Payment created',
                'payment': payment.to_dict()
            }), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}")
            return jsonify({'error': 'Failed to initiate payment'}), 500

    @staticmethod
    def check_payment_status(current_user, payment_reference):
        """Check payment status"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            payment_service = PaymentService()
            payment = payment_service.get_payment_by_reference(payment_reference)

            if not payment:
                return jsonify({'error': 'Payment not found'}), 404

            # Check if user owns the payment
            if payment.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403

            # For M-Pesa payments, check status
            if payment.payment_method == 'mpesa' and payment.checkout_request_id:
                try:
                    status_response = payment_service.check_payment_status(payment.checkout_request_id)

                    # Get updated payment
                    payment = payment_service.get_payment_by_id(payment.id)
                    return jsonify({
                        'payment': payment.to_dict(),
                        'status_check': status_response
                    }), 200
                except Exception as status_error:
                    logger.error(f"Status check failed: {str(status_error)}")
                    # Still return payment data even if status check failed
                    return jsonify({
                        'payment': payment.to_dict(),
                        'status_check_error': str(status_error)
                    }), 200

            return jsonify({'payment': payment.to_dict()}), 200

        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return jsonify({'error': 'Failed to check payment status'}), 500

    @staticmethod
    def mpesa_callback(current_user):
        """Handle M-Pesa STK Push callback"""
        try:
            data = request.get_json()
            logger.info(f"📩 M-Pesa callback received: {json.dumps(data, indent=2)}")

            payment_service = PaymentService()
            response = payment_service.process_mpesa_callback(data)

            return jsonify(response), 200

        except Exception as e:
            logger.error(f"❌ Error processing M-Pesa callback: {str(e)}")
            return jsonify({"ResultCode": 1, "ResultDesc": "Internal server error"}), 500

    @staticmethod
    def process_refund(current_user, payment_id):
        """Process payment refund (admin only)"""
        try:
            current_user = get_current_user()
            if not current_user or current_user.role not in ['admin', 'brand_admin']:
                return jsonify({'error': 'Unauthorized'}), 401

            data = request.get_json()
            required_fields = ['refund_amount', 'refund_reason']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            payment_service = PaymentService()
            payment = payment_service.get_payment_by_id(payment_id)

            if not payment:
                return jsonify({'error': 'Payment not found'}), 404

            # Validate refund amount
            if float(data['refund_amount']) > payment.amount:
                return jsonify({'error': 'Refund amount cannot exceed payment amount'}), 400

            # Update payment with refund info
            payment.refund_amount = float(data['refund_amount'])
            payment.refund_reason = data['refund_reason']
            payment.status = 'refunded'
            payment.updated_at = datetime.utcnow()

            # Update order status
            order = Order.query.get(payment.order_id)
            if order:
                order.status = 'refunded'
                order.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'message': 'Refund processed successfully',
                'payment': payment.to_dict()
            }), 200

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return jsonify({'error': 'Failed to process refund'}), 500

    @staticmethod
    def get_payment_stats(current_user):
        """Get payment statistics"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            payment_service = PaymentService()

            if current_user.role == 'customer':
                user_payments = payment_service.get_user_payments(current_user.id)

                stats = {
                    'total_payments': user_payments['total'],
                    'total_amount': sum(p.amount for p in user_payments['payments']),
                    'successful_payments': sum(1 for p in user_payments['payments'] if p.status == 'completed'),
                    'pending_payments': sum(1 for p in user_payments['payments'] if p.status == 'pending'),
                    'failed_payments': sum(1 for p in user_payments['payments'] if p.status == 'failed')
                }
            else:
                # For admins, get all payments stats
                # Note: You might want to implement this differently for performance
                all_payments = Payment.query.all()

                stats = {
                    'total_payments': len(all_payments),
                    'total_amount': sum(p.amount for p in all_payments),
                    'successful_payments': sum(1 for p in all_payments if p.status == 'completed'),
                    'pending_payments': sum(1 for p in all_payments if p.status == 'pending'),
                    'failed_payments': sum(1 for p in all_payments if p.status == 'failed'),
                    'refunded_payments': sum(1 for p in all_payments if p.status == 'refunded')
                }

            return jsonify(stats), 200

        except Exception as e:
            logger.error(f"Error getting payment stats: {str(e)}")
            return jsonify({'error': 'Failed to get payment statistics'}), 500