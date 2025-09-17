from app.extensions import db

class TShirt(db.Model):
    __tablename__ = 'tshirts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    style_tag = db.Column(db.String(50), nullable=False)  # e.g., "artsy", "afrobeat", "rock"
    artist = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)

    # ✅ use back_populates (not backref) to sync with Order model
    orders = db.relationship("Order", back_populates="tshirt", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'price': self.price,
            'category': self.category,
            'style_tag': self.style_tag,
            'artist': self.artist,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
