from backend_app.extensions import db
from datetime import datetime


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    payment_reference = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='KES')
    status = db.Column(db.String(20), default="pending")  # pending, processing, completed, failed, refunded
    payment_method = db.Column(db.String(50))  # mpesa, card, bank_transfer
    provider = db.Column(db.String(50))  # safaricom, stripe, paypal
    transaction_id = db.Column(db.String(100))
    merchant_request_id = db.Column(db.String(100))
    checkout_request_id = db.Column(db.String(100))
    result_code = db.Column(db.Integer)
    result_description = db.Column(db.String(255))
    mpesa_receipt_number = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    account_number = db.Column(db.String(50))
    card_last_four = db.Column(db.String(4))
    card_brand = db.Column(db.String(50))
    refund_amount = db.Column(db.Float, default=0.0)
    refund_reason = db.Column(db.Text)
    metadata = db.Column(db.JSON)  # Additional payment data
    initiated_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship("User", back_populates="payments")
    order = db.relationship("Order", back_populates="payments")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.payment_reference:
            self.payment_reference = self.generate_payment_reference()

    def generate_payment_reference(self):
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        import random
        random_num = random.randint(1000, 9999)
        return f'PAY-{timestamp}-{random_num}'

    def to_dict(self):
        return {
            'id': self.id,
            'payment_reference': self.payment_reference,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'provider': self.provider,
            'transaction_id': self.transaction_id,
            'merchant_request_id': self.merchant_request_id,
            'checkout_request_id': self.checkout_request_id,
            'result_code': self.result_code,
            'result_description': self.result_description,
            'mpesa_receipt_number': self.mpesa_receipt_number,
            'phone_number': self.phone_number,
            'account_number': self.account_number,
            'card_last_four': self.card_last_four,
            'card_brand': self.card_brand,
            'refund_amount': self.refund_amount,
            'refund_reason': self.refund_reason,
            'metadata': self.metadata,
            'initiated_at': self.initiated_at.isoformat() if self.initiated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None
        }