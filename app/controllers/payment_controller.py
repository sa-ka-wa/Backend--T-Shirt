from flask import request, jsonify
from app.extensions import db
from app.models.payment import Payment
from app.services.payment_service import PaymentService


class PaymentController:
    @staticmethod
    def get_payments():
        payments = PaymentService.get_all_payments()
        return jsonify([payment.to_dict() for payment in payments])

    @staticmethod
    def get_payment(payment_id):
        payment = PaymentService.get_payment_by_id(payment_id)
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        return jsonify(payment.to_dict())

    @staticmethod
    def create_payment():
        data = request.get_json()

        # Validate required fields
        required_fields = ['order_id', 'amount', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        payment = PaymentService.create_payment(
            data['order_id'],
            data['amount'],
            data['payment_method'],
            data.get('status', 'pending')
        )

        return jsonify(payment.to_dict()), 201

    @staticmethod
    def update_payment(payment_id):
        data = request.get_json()
        payment = PaymentService.update_payment(payment_id, data)

        if not payment:
            return jsonify({'error': 'Payment not found'}), 404

        return jsonify(payment.to_dict())