from app.extensions import db

class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, completed, failed
    method = db.Column(db.String(50))  # mpesa, paypal, etc.
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # relationships
    user = db.relationship("User", back_populates="payments")
    order = db.relationship("Order", back_populates="payments")
