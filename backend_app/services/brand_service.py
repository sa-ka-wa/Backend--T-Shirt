# backend_app/services/brand_service.py
from backend_app.extensions import db
from backend_app.models.brand import Brand

class BrandService:
    @staticmethod
    def get_all_brands():
        return Brand.query.filter_by(is_active=True).all()

    @staticmethod
    def get_brands_by_category(category):
        return Brand.query.filter_by(category=category, is_active=True).all()

    @staticmethod
    def get_brand_by_id(brand_id):
        return Brand.query.filter_by(id=brand_id, is_active=True).first()

    @staticmethod
    def create_brand(current_user,name, category, description=None, logo_url=None, website=None, established_year=None):
        """Create a new brand (super_admin only)."""
        if current_user.role != 'super_admin':
            raise PermissionError("Unauthorized: Only super_admin can create a brand.")


        brand = Brand(
            name=name,
            description=description,
            logo_url=logo_url,
            website=website,
            established_year=established_year,
            category=category
        )
        db.session.add(brand)
        db.session.commit()
        return brand

    @staticmethod
    def update_brand(current_user,brand_id, data):
        """Update a brand (super_admin only)."""
        if current_user.role != 'super_admin':
            raise PermissionError("Unauthorized: Only super_admin can update a brand.")


        brand = BrandService.get_brand_by_id(brand_id)
        if not brand:
            return None

        for key, value in data.items():
            if hasattr(brand, key):
                setattr(brand, key, value)

        db.session.commit()
        return brand

    @staticmethod
    def delete_brand(current_user,brand_id):
        """Soft delete a brand (super_admin only)."""
        if current_user.role != 'super_admin':
            raise PermissionError("Unauthorized: Only super_admin can delete a brand.")


        brand = BrandService.get_brand_by_id(brand_id)
        if not brand:
            return False

        brand.is_active = False
        db.session.commit()
        return True

    @staticmethod
    def get_brand_tshirts(brand_id):
        brand = BrandService.get_brand_by_id(brand_id)
        if not brand:
            return None
        return brand.tshirts