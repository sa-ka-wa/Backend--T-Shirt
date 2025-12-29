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
    def create_brand(current_user):

        """Restricted: Only super_admin can create a brand"""
        if current_user.role != 'super_admin':
            return jsonify({'error': 'Unauthorized: Only super_admin can create brands'}), 403

        data = request.get_json()
        name = data.get("name")

        # generate subdomain safely
        subdomain = name.lower().replace(" ", "-")
        website = f"https://{subdomain}.lvh.me:3004"

        # Validate required fields
        required_fields = ['name', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        brand = BrandService.create_brand(
            name=name,
            description=data.get("description"),
            established_year=data.get("established_year"),
            logo_url=data.get("logo_url"),
            category=data.get("category"),
            website=website,
            subdomain=subdomain
        )

        return jsonify(brand.to_dict()), 201

    @staticmethod
    def update_brand(current_user, brand_id):
        """Restricted: Only super_admin can update a brand"""
        if current_user.role != 'super_admin':
            return jsonify({'error': 'Unauthorized: Only super_admin can update brands'}), 403

        data = request.get_json()
        brand = BrandService.update_brand(current_user,brand_id, data)

        if not brand:
            return jsonify({'error': 'Brand not found'}), 404

        return jsonify(brand.to_dict())

    @staticmethod
    def delete_brand(current_user, brand_id):
        """Restricted: Only super_admin can delete a brand"""
        if current_user.role != 'super_admin':
            return jsonify({'error': 'Unauthorized: Only super_admin can delete brands'}), 403

        success = BrandService.delete_brand(current_user,brand_id)

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
    @staticmethod
    def get_brand_by_subdomain():
        subdomain = request.args.get("subdomain")
        if not subdomain:
            return jsonify({"error": "Missing subdomain parameter"}), 400

            # Try to find the brand by subdomain
        brand = Brand.query.filter_by(subdomain=subdomain).first()

        # If brand not found by subdomain, check if any brand has NULL subdomain and matches name
        if not brand:
            # Search for a brand whose name lowercased with hyphens matches requested subdomain
            candidate = Brand.query.filter_by(subdomain=None).all()
            for b in candidate:
                generated = b.name.lower().replace(" ", "-")
                if generated == subdomain:
                    # Update the brand with the subdomain
                    b.subdomain = subdomain
                    db.session.commit()
                    brand = b
                    break

        if not brand:
            return jsonify({"error": f"Brand not found for subdomain '{subdomain}'"}), 404

        return jsonify(brand.to_dict()), 200
    @staticmethod
    def update_subdomain():
        data = request.get_json()
        subdomain = data.get("subdomain")

        if not subdomain:
            return jsonify({"error": "Subdomain is required"}), 400

        # Check if brand exists for this subdomain
        brand = Brand.query.filter_by(subdomain=subdomain).first()
        if brand:
            return jsonify({"message": "Subdomain already exists", "brand": brand.to_dict()}), 200

        # Otherwise, create new brand entry or log it
        new_brand = Brand(name=subdomain.capitalize(), subdomain=subdomain)
        new_brand.category = data.get("category", "general")


        db.session.add(new_brand)
        db.session.commit()

        return jsonify({
            "message": f"New brand '{subdomain}' added successfully",
            "brand": new_brand.to_dict()
        }), 201