from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.tshirt import TShirt
from backend_app.services.tshirt_service import TShirtService


class TShirtController:
    @staticmethod
    def get_all_tshirts():
        """Get all t-shirts, optionally filtered by style tag"""
        style_tag = request.args.get('style')
        tshirts = TShirtService.get_tshirts_by_style(style_tag) if style_tag else TShirtService.get_all_tshirts()
        return jsonify([tshirt.to_dict() for tshirt in tshirts])

    @staticmethod
    def get_tshirt(tshirt_id):
        """Get a specific t-shirt by ID"""
        tshirt = TShirtService.get_tshirt_by_id(tshirt_id)
        if not tshirt:
            return jsonify({'error': 'T-shirt not found'}), 404
        return jsonify(tshirt.to_dict())

    @staticmethod
    def create_tshirt():
        """Create a new t-shirt (admin only)"""
        data = request.get_json()

        # Validate required fields
        required_fields = ['title', 'image_url', 'price', 'style_tag']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        tshirt = TShirtService.create_tshirt(
            data['title'],
            data['image_url'],
            data['price'],
            data['style_tag'],
            data.get('description'),
            data.get('category'),
            data.get('artist')
        )

        return jsonify(tshirt.to_dict()), 201

    @staticmethod
    def update_tshirt(tshirt_id):
        """Update a t-shirt (admin only)"""
        data = request.get_json()
        tshirt = TShirtService.update_tshirt(tshirt_id, data)

        if not tshirt:
            return jsonify({'error': 'T-shirt not found'}), 404

        return jsonify(tshirt.to_dict())

    @staticmethod
    def delete_tshirt(tshirt_id):
        """Delete a t-shirt (admin only)"""
        success = TShirtService.delete_tshirt(tshirt_id)

        if not success:
            return jsonify({'error': 'T-shirt not found'}), 404

        return jsonify({'message': 'T-shirt deleted successfully'}), 200