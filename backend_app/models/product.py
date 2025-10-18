# backend_app/models/product.py
from backend_app.extensions import db


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)  # "tshirt", "hoodie", "bandana", "cap"
    product_type = db.Column(db.String(50), nullable=False)  # "clothing", "accessory"
    style_tag = db.Column(db.String(50), nullable=False)  # "artsy", "afrobeat", "rock"
    artist = db.Column(db.String(100))
    size = db.Column(db.String(20))  # "S", "M", "L", "XL", "One Size"
    color = db.Column(db.String(50))
    material = db.Column(db.String(100))
    stock_quantity = db.Column(db.Integer, default=0)

    # NEW: 3D Model fields
    model_3d_url = db.Column(db.String(500))  # URL to .glb file
    has_3d_model = db.Column(db.Boolean, default=False)
    model_scale = db.Column(db.Float, default=1.0)  # Scale for 3D model
    model_position = db.Column(db.JSON)  # {x: 0, y: 0, z: 0}

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)

    # Brand relationship
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'))
    brand = db.relationship("Brand", back_populates="products")

    # Order relationship
    orders = db.relationship("Order", back_populates="product", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'price': self.price,
            'category': self.category,
            'product_type': self.product_type,
            'style_tag': self.style_tag,
            'artist': self.artist,
            'size': self.size,
            'color': self.color,
            'material': self.material,
            'stock_quantity': self.stock_quantity,
            'has_3d_model': self.has_3d_model,
            'model_3d_url': self.model_3d_url,
            'model_scale': self.model_scale,
            'model_position': self.model_position,
            'brand_id': self.brand_id,
            'brand_name': self.brand.name if self.brand else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }