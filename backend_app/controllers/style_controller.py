from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.theme import Theme
from backend_app.services.style_service import StyleService


class StyleController:
    @staticmethod
    def get_theme_by_style_tag(style_tag):
        """Get theme configuration by style tag"""
        theme = StyleService.get_theme_by_style_tag(style_tag)
        if not theme:
            return jsonify({'error': 'Theme not found'}), 404

        return jsonify(theme.to_dict())

    @staticmethod
    def get_all_themes():
        """Get all available themes"""
        themes = StyleService.get_all_themes()
        return jsonify([theme.to_dict() for theme in themes])

    @staticmethod
    def create_theme():
        """Create a new theme (admin only)"""
        data = request.get_json()

        # Validate required fields
        required_fields = ['style_tag', 'name', 'colors', 'fonts', 'layout_config']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        theme = StyleService.create_theme(
            data['style_tag'],
            data['name'],
            data['colors'],
            data['fonts'],
            data['layout_config']
        )

        return jsonify(theme.to_dict()), 201