# app/services/product_service.py
from app.extensions import db
from app.models.product import Product

class ProductService:
    @staticmethod
    def get_all_products():
        return Product.query.filter_by(is_active=True).all()

    @staticmethod
    def get_products_by_category(category):
        return Product.query.filter_by(category=category, is_active=True).all()

    @staticmethod
    def get_products_by_type(product_type):
        return Product.query.filter_by(product_type=product_type, is_active=True).all()

    @staticmethod
    def get_products_by_style(style_tag):
        return Product.query.filter_by(style_tag=style_tag, is_active=True).all()

    @staticmethod
    def get_products_by_brand(brand_id):
        return Product.query.filter_by(brand_id=brand_id, is_active=True).all()

    @staticmethod
    def get_product_by_id(product_id):
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @staticmethod
    def search_products(query):
        return Product.query.filter(
            Product.is_active == True,
            (Product.title.ilike(f'%{query}%') |
             Product.description.ilike(f'%{query}%') |
             Product.artist.ilike(f'%{query}%'))
        ).all()

    @staticmethod
    def create_product(title, image_url, price, category, product_type, style_tag,
                      description=None, artist=None, size=None, color=None,
                      material=None, stock_quantity=0, brand_id=None):
        product = Product(
            title=title,
            description=description,
            image_url=image_url,
            price=price,
            category=category,
            product_type=product_type,
            style_tag=style_tag,
            artist=artist,
            size=size,
            color=color,
            material=material,
            stock_quantity=stock_quantity,
            brand_id=brand_id
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def update_product(product_id, data):
        product = ProductService.get_product_by_id(product_id)
        if not product:
            return None

        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        db.session.commit()
        return product

    @staticmethod
    def delete_product(product_id):
        product = ProductService.get_product_by_id(product_id)
        if not product:
            return False

        product.is_active = False
        db.session.commit()
        return True

    @staticmethod
    def update_stock(product_id, quantity):
        product = ProductService.get_product_by_id(product_id)
        if not product:
            return None

        product.stock_quantity = quantity
        db.session.commit()
        return product