from app.extensions import db
from app.utils.password_helper import hash_password


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='customer')
    preferences = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # relationships
    orders = db.relationship('Order', backref='user', lazy=True)
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }