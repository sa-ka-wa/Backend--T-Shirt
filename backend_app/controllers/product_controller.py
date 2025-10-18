# backend_app/controllers/product_controller.py
from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.product import Product
from backend_app.services.product_service import ProductService


class ProductController:
    @staticmethod
    def get_all_products():
        """Get all products with optional filtering"""
        category = request.args.get('category')
        product_type = request.args.get('type')
        style_tag = request.args.get('style')
        brand_id = request.args.get('brand_id')
        search = request.args.get('search')

        if search:
            products = ProductService.search_products(search)
        elif category:
            products = ProductService.get_products_by_category(category)
        elif product_type:
            products = ProductService.get_products_by_type(product_type)
        elif style_tag:
            products = ProductService.get_products_by_style(style_tag)
        elif brand_id:
            products = ProductService.get_products_by_brand(brand_id)
        else:
            products = ProductService.get_all_products()

        return jsonify([product.to_dict() for product in products])

    @staticmethod
    def get_product(product_id):
        """Get a specific product by ID"""
        product = ProductService.get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify(product.to_dict())

    @staticmethod
    def create_product():
        """Create a new product (admin only)"""
        data = request.get_json()

        # Validate required fields
        required_fields = ['title', 'image_url', 'price', 'category', 'product_type', 'style_tag']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        product = ProductService.create_product(
            data['title'],
            data['image_url'],
            data['price'],
            data['category'],
            data['product_type'],
            data['style_tag'],
            data.get('description'),
            data.get('artist'),
            data.get('size'),
            data.get('color'),
            data.get('material'),
            data.get('stock_quantity', 0),
            data.get('brand_id')
        )

        return jsonify(product.to_dict()), 201

    @staticmethod
    def update_product(product_id):
        """Update a product (admin only)"""
        data = request.get_json()
        product = ProductService.update_product(product_id, data)

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        return jsonify(product.to_dict())

    @staticmethod
    def delete_product(product_id):
        """Delete a product (admin only)"""
        success = ProductService.delete_product(product_id)

        if not success:
            return jsonify({'error': 'Product not found'}), 404

        return jsonify({'message': 'Product deleted successfully'}), 200

    @staticmethod
    def update_stock(product_id):
        """Update product stock quantity (admin only)"""
        data = request.get_json()

        if 'stock_quantity' not in data:
            return jsonify({'error': 'stock_quantity is required'}), 400

        product = ProductService.update_stock(product_id, data['stock_quantity'])

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        return jsonify(product.to_dict())