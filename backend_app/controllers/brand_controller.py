# backend_app/controllers/brand_controller.py
from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.brand import Brand
from backend_app.services.brand_service import BrandService


class BrandController:
    @staticmethod
    def get_all_brands():
        """Get all brands, optionally filtered by category"""
        category = request.args.get('category')
        brands = BrandService.get_brands_by_category(category) if category else BrandService.get_all_brands()
        return jsonify([brand.to_dict() for brand in brands])

    @staticmethod
    def get_brand(brand_id):
        """Get a specific brand by ID"""
        brand = BrandService.get_brand_by_id(brand_id)
        if not brand:
            return jsonify({'error': 'Brand not found'}), 404
        return jsonify(brand.to_dict())

    @staticmethod
    def create_brand():
        """Create a new brand (admin only)"""
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        brand = BrandService.create_brand(
            data['name'],
            data['category'],
            data.get('description'),
            data.get('logo_url'),
            data.get('website'),
            data.get('established_year')
        )

        return jsonify(brand.to_dict()), 201

    @staticmethod
    def update_brand(brand_id):
        """Update a brand (admin only)"""
        data = request.get_json()
        brand = BrandService.update_brand(brand_id, data)

        if not brand:
            return jsonify({'error': 'Brand not found'}), 404

        return jsonify(brand.to_dict())

    @staticmethod
    def delete_brand(brand_id):
        """Delete a brand (admin only)"""
        success = BrandService.delete_brand(brand_id)

        if not success:
            return jsonify({'error': 'Brand not found'}), 404

        return jsonify({'message': 'Brand deleted successfully'}), 200

    @staticmethod
    def get_brand_tshirts(brand_id):
        """Get all t-shirts for a specific brand"""
        tshirts = BrandService.get_brand_tshirts(brand_id)

        if tshirts is None:
            return jsonify({'error': 'Brand not found'}), 404

        return jsonify([tshirt.to_dict() for tshirt in tshirts])