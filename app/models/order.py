# app/models/order.py
from app.extensions import db

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    shipping_status = db.Column(db.String(20), default='processing')
    shipping_address = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # ✅ Fix relationships
    user = db.relationship("User", back_populates="orders")  # <— add this line
    payments = db.relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    product = db.relationship("Product", back_populates="orders")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'shipping_status': self.shipping_status,
            'shipping_address': self.shipping_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'product': self.product.to_dict() if self.product else None
        }
