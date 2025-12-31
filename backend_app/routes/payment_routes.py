from flask import Blueprint
from backend_app.controllers.payment_controller import PaymentController
from backend_app.utils.jwt_helper import token_required

payment_bp = Blueprint('payment', __name__)


# Get all payments
@payment_bp.route('/', methods=['GET'])
@token_required
def get_payments():
    return PaymentController.get_payments()


# Get payment statistics
@payment_bp.route('/stats', methods=['GET'])
@token_required
def get_payment_stats():
    return PaymentController.get_payment_stats()


# Get specific payment
@payment_bp.route('/<int:payment_id>', methods=['GET'])
@token_required
def get_payment(payment_id):
    return PaymentController.get_payment(payment_id)


# Initiate payment
@payment_bp.route('/initiate', methods=['POST'])
@token_required
def initiate_payment():
    return PaymentController.initiate_payment()


# Check payment status
@payment_bp.route('/status/<string:payment_reference>', methods=['GET'])
@token_required
def check_payment_status(payment_reference):
    return PaymentController.check_payment_status(payment_reference)


# Process refund
@payment_bp.route('/<int:payment_id>/refund', methods=['POST'])
@token_required
def process_refund(payment_id):
    return PaymentController.process_refund(payment_id)


# M-Pesa callback (no auth required)
@payment_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    return PaymentController.mpesa_callback()


# M-Pesa STK Push
@payment_bp.route('/mpesa/stk-push', methods=['POST'])
@token_required
def mpesa_stk_push():
    return PaymentController.initiate_payment()


# Test payment endpoint (for development)
@payment_bp.route('/test', methods=['POST'])
def test_payment():
    from flask import jsonify
    from datetime import datetime
    import random

    # Simulate a successful payment for testing
    return jsonify({
        'success': True,
        'message': 'Test payment successful',
        'transaction_id': f'TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}-{random.randint(1000, 9999)}',
        'timestamp': datetime.utcnow().isoformat()
    }), 200