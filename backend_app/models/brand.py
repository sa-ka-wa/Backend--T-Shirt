# backend_app/models/brand.py
from backend_app.extensions import db

class Brand(db.Model):
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), nullable=True, unique=True)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    website = db.Column(db.String(200))
    contact_email = db.Column(db.String(100))
    established_year = db.Column(db.Integer)
    subdomain = db.Column(db.String(50), nullable=True, unique=True)
    category = db.Column(db.String(100), nullable=False)  # e.g., "clothing", "lifestyle", "sports"
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)

    # Relationship with TShirts
    # tshirts = db.relationship("TShirt", back_populates="brand", cascade="all, delete-orphan")
    users = db.relationship('User', back_populates='brand', cascade='all, delete-orphan')
    products = db.relationship("Product", back_populates="brand", cascade="all, delete-orphan")

    def to_dict(self, include_users=False, include_products=False):
        data =  {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'logo_url': self.logo_url,
            'website': self.website,
            'contact_email': self.contact_email,
            'established_year': self.established_year,
            'subdomain': self.subdomain,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            # 'tshirts_count': len(self.tshirts) if self.tshirts else 0,
            'products_count': len(self.products) if self.products else 0
        }
        if include_users:
            data["users"] = [user.to_dict() for user in self.users]

        if include_products:
            data["products"] = [product.to_dict() for product in self.products]

        return data

