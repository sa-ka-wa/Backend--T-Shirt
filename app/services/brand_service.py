# app/services/brand_service.py
from app.extensions import db
from app.models.brand import Brand

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
    def create_brand(name, category, description=None, logo_url=None, website=None, established_year=None):
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
    def update_brand(brand_id, data):
        brand = BrandService.get_brand_by_id(brand_id)
        if not brand:
            return None

        for key, value in data.items():
            if hasattr(brand, key):
                setattr(brand, key, value)

        db.session.commit()
        return brand

    @staticmethod
    def delete_brand(brand_id):
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