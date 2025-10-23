from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.product import Product
from backend_app.services.product_service import ProductService
from backend_app.utils.brand_filter import brand_filtered_query


class ProductController:
    @staticmethod
    def get_all_products():
        """Get all products with optional filtering"""
        category = request.args.get('category')
        product_type = request.args.get('type')
        style_tag = request.args.get('style')
        brand_id = request.args.get('brand_id')
        search = request.args.get('search')

        # ✅ Brand-filtered query (auto restricts admin by their brand)
        query = brand_filtered_query(Product).filter_by(is_active=True)

        # Apply additional filters
        if search:
            query = query.filter(
                (Product.title.ilike(f'%{search}%')) |
                (Product.description.ilike(f'%{search}%')) |
                (Product.artist.ilike(f'%{search}%'))
            )
        if category:
            query = query.filter_by(category=category)
        if product_type:
            query = query.filter_by(product_type=product_type)
        if style_tag:
            query = query.filter_by(style_tag=style_tag)
        if brand_id:
            query = query.filter_by(brand_id=brand_id)

        products = query.all()
        return jsonify([product.to_dict() for product in products]), 200

    @staticmethod
    def get_product(product_id):
        """Get a specific product by ID"""
        product = ProductService.get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify(product.to_dict()), 200

    @staticmethod
    def create_product(current_user):
        """Create a new product (admin/super_admin only)"""
        data = request.get_json()

        # ✅ Validate required fields
        required_fields = ['title', 'image_url', 'price', 'category', 'product_type', 'style_tag']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # ✅ Enforce brand rules
        if current_user.role == 'admin':
            brand_id = current_user.brand_id
        elif current_user.role == 'super_admin':
            brand_id = data.get('brand_id')
            if not brand_id:
                return jsonify({'error': 'brand_id is required for super_admin'}), 400
        else:
            return jsonify({'error': 'Unauthorized role'}), 403

        # ✅ Create product
        product = ProductService.create_product(
            current_user,
            title=data['title'],
            image_url=data['image_url'],
            price=data['price'],
            category=data['category'],
            product_type=data['product_type'],
            style_tag=data['style_tag'],
            description=data.get('description'),
            artist=data.get('artist'),
            size=data.get('size'),
            color=data.get('color'),
            material=data.get('material'),
            stock_quantity=data.get('stock_quantity', 0),
            brand_id=brand_id,
            has_3d_model=data.get('has_3d_model', False),
            model_3d_url=data.get('model_3d_url'),
            model_scale=data.get('model_scale', 1.0),
            model_position=data.get('model_position'),
            is_active=data.get('is_active', True)
        )

        return jsonify(product.to_dict()), 201

    @staticmethod
    def update_product(current_user, product_id):
        """Update a product (admin/super_admin only)"""
        data = request.get_json()
        product = ProductService.get_product_by_id(product_id)

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # ✅ Brand ownership enforcement
        if current_user.role == 'admin' and product.brand_id != current_user.brand_id:
            return jsonify({'error': 'Unauthorized: Cannot modify another brand’s product'}), 403
        elif current_user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Unauthorized role'}), 403

        # ✅ Update once
        updated_product = ProductService.update_product(current_user,product_id, data)
        return jsonify(updated_product.to_dict()), 200

    @staticmethod
    def delete_product(current_user, product_id):
        """Delete a product (admin/super_admin only)"""
        product = ProductService.get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # ✅ Brand-level restriction
        if current_user.role == 'admin' and product.brand_id != current_user.brand_id:
            return jsonify({'error': 'Unauthorized: Cannot delete another brand’s product'}), 403
        elif current_user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Unauthorized role'}), 403

        ProductService.delete_product(current_user,product_id)
        return jsonify({'message': 'Product deleted successfully'}), 200

    @staticmethod
    def update_stock(current_user, product_id):
        """Update product stock quantity (admin/super_admin only)"""
        data = request.get_json()

        if 'stock_quantity' not in data:
            return jsonify({'error': 'stock_quantity is required'}), 400

        product = ProductService.get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # ✅ Brand-level restriction
        if current_user.role == 'admin' and product.brand_id != current_user.brand_id:
            return jsonify({'error': 'Unauthorized: Cannot update another brand’s product stock'}), 403
        elif current_user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Unauthorized role'}), 403

        updated_product = ProductService.update_stock(current_user,product_id, data['stock_quantity'])
        return jsonify(updated_product.to_dict()), 200
