from app.extensions import db
from app.models.payment import Payment


class PaymentService:
    @staticmethod
    def get_all_payments():
        return Payment.query.all()

    @staticmethod
    def get_payment_by_id(payment_id):
        return Payment.query.get(payment_id)

    @staticmethod
    def create_payment(order_id, amount, payment_method, status='pending'):
        payment = Payment(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            status=status
        )

        db.session.add(payment)
        db.session.commit()
        return payment

    @staticmethod
    def update_payment(payment_id, data):
        payment = Payment.query.get(payment_id)
        if not payment:
            return None

        for key, value in data.items():
            if hasattr(payment, key) and key != 'id':
                setattr(payment, key, value)

        db.session.commit()
        return payment