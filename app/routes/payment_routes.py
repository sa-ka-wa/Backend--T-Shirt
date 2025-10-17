from flask import Blueprint
from app.controllers.payment_controller import PaymentController
from app.utils.jwt_helper import token_required

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/', methods=['GET'])
@token_required
def get_payments():
    return PaymentController.get_payments()

@payment_bp.route('/<int:payment_id>', methods=['GET'])
@token_required
def get_payment(payment_id):
    return PaymentController.get_payment(payment_id)

@payment_bp.route('/', methods=['POST'])
@token_required
def create_payment():
    return PaymentController.create_payment()

@payment_bp.route('/<int:payment_id>', methods=['PUT'])
@token_required
def update_payment(payment_id):
    return PaymentController.update_payment(payment_id)

@payment_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """
    This is called by Safaricom when the M-Pesa transaction finishes.
    No authentication is required.
    """
    return PaymentController.mpesa_callback()