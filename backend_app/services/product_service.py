# backend_app/services/product_service.py
from backend_app.extensions import db
from backend_app.models.product import Product
from backend_app.models.brand import Brand
from sqlalchemy.exc import SQLAlchemyError

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
    def create_product(current_user,title, image_url, price, category, product_type, style_tag,
                      description=None, artist=None, size=None, color=None,
                      material=None, stock_quantity=0, brand_id=None,
                   has_3d_model=False, model_3d_url=None, model_scale=1.0, model_position=None,
                   is_active=True):

        """Create a new product - Only admin/super_admin"""
        if current_user.role not in ['admin', 'super_admin']:
            raise PermissionError("Unauthorized: Only admin or super_admin can create products")

        # Check for duplicate title
        if Product.query.filter_by(title=title, is_active=True).first():
            raise ValueError("Product with this title already exists")

        # Validate brand_id if provided
        if brand_id and not Brand.query.get(brand_id):
            raise ValueError("Invalid brand_id: brand does not exist")

        try:
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
                brand_id=brand_id,
                has_3d_model=has_3d_model,
                model_3d_url=model_3d_url,
                model_scale=model_scale,
                model_position=model_position,
                is_active=is_active
            )
            db.session.add(product)  # ✅ Fixed indentation
            db.session.commit()
            return product

        except SQLAlchemyError as e:
            db.session.rollback()
            raise RuntimeError(f"Database error while creating product: {str(e)}")

    @staticmethod
    def update_product(current_user, product_id, data):
        """Update a product - Only admin/super_admin"""
        if current_user.role not in ['admin', 'super_admin']:
            raise PermissionError("Unauthorized: Only admin or super_admin can update products")

        product = ProductService.get_product_by_id(product_id)
        if not product:
            return None

        try:
            for key, value in data.items():
                if hasattr(product, key):
                    setattr(product, key, value)

            db.session.commit()
            return product
        except SQLAlchemyError as e:
            db.session.rollback()
            raise RuntimeError(f"Database error while updating product: {str(e)}")

    @staticmethod
    def delete_product(current_user, product_id):
        """Soft delete a product - Only admin/super_admin"""
        if current_user.role not in ['admin', 'super_admin']:
            raise PermissionError("Unauthorized: Only admin or super_admin can delete products")

        product = ProductService.get_product_by_id(product_id)
        if not product:
            return False

        try:
            product.is_active = False
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise RuntimeError(f"Database error while deleting product: {str(e)}")

    @staticmethod
    def update_stock(current_user, product_id, quantity):
        """Update product stock - Only admin/super_admin"""
        if current_user.role not in ['admin', 'super_admin']:
            raise PermissionError("Unauthorized: Only admin or super_admin can update stock")

        product = ProductService.get_product_by_id(product_id)
        if not product:
            return None

        try:
            product.stock_quantity = quantity
            db.session.commit()
            return product
        except SQLAlchemyError as e:
            db.session.rollback()
            raise RuntimeError(f"Database error while updating stock: {str(e)}")