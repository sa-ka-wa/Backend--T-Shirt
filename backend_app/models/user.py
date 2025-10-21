# backend_app/models/user.py
from backend_app.extensions import db
from backend_app.utils.password_helper import hash_password

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), default='customer')
    preferences = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    brand = db.relationship('Brand', back_populates='users')
    orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'preferences': self.preferences,
            'brand_id': self.brand_id,
            'brand_name': self.brand.name if self.brand else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }