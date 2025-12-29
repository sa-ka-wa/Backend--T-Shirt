from backend_app.extensions import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id'),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='orders')
    product = db.relationship('Product', back_populates='orders')
    payments = db.relationship('Payment', back_populates='order', cascade='all, delete-orphan')


    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_amount': self.total_amount,
            'shipping_address': self.shipping_address,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
