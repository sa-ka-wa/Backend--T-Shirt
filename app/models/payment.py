# app/models/payment.py
from app.extensions import db

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    merchant_request_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default="pending")
    method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    user = db.relationship("User", back_populates="payments")
    order = db.relationship("Order", back_populates="payments")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'amount': self.amount,
            'status': self.status,
            'method': self.method,
            'transaction_id': self.transaction_id,
            'merchant_request_id': self.merchant_request_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }