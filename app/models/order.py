from app.extensions import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tshirt_id = db.Column(db.Integer, db.ForeignKey('tshirts.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    shipping_status = db.Column(db.String(20), default='processing')  # processing, shipped, delivered
    shipping_address = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


    # ✅ Relationships
    payments = db.relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    tshirt = db.relationship("TShirt", back_populates="orders")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tshirt_id': self.tshirt_id,
            'quantity': self.quantity,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'shipping_status': self.shipping_status,
            'shipping_address': self.shipping_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tshirt': self.tshirt.to_dict() if self.tshirt else None
        }