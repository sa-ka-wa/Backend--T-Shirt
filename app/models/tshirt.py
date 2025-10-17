# app/models/tshirt.py
from app.extensions import db

class TShirt(db.Model):
    __tablename__ = 'tshirts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    style_tag = db.Column(db.String(50), nullable=False)
    artist = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)

    # Add brand relationship
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'))
    # brand = db.relationship("Brand", back_populates="tshirts")

    # Fix orders relationship - use backref instead of back_populates
    # orders = db.relationship("Order", backref="tshirt", lazy=True, cascade="all, delete-orphan")

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
            'brand_id': self.brand_id,
            'brand_name': self.brand.name if self.brand else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }