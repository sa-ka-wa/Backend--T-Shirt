import re
from flask import jsonify


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_tshirt_data(data):
    errors = []

    if not data.get('title') or len(data['title']) < 2:
        errors.append('T-shirt title must be at least 2 characters long')

    if not data.get('image_url'):
        errors.append('Image URL is required')

    if not data.get('price') or float(data['price']) <= 0:
        errors.append('Price must be greater than 0')

    if not data.get('style_tag'):
        errors.append('Style tag is required')

    return errors


def validate_order_data(data):
    errors = []

    if not data.get('tshirt_id'):
        errors.append('T-shirt ID is required')

    if not data.get('quantity') or int(data['quantity']) <= 0:
        errors.append('Quantity must be at least 1')

    if not data.get('shipping_address'):
        errors.append('Shipping address is required')

    return errors


def validate_theme_data(data):
    errors = []

    if not data.get('style_tag'):
        errors.append('Style tag is required')

    if not data.get('name'):
        errors.append('Theme name is required')

    if not data.get('colors'):
        errors.append('Colors configuration is required')

    if not data.get('fonts'):
        errors.append('Fonts configuration is required')

    if not data.get('layout_config'):
        errors.append('Layout configuration is required')

    return errors