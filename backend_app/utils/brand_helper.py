# backend_app/utils/brand_helper.py
from backend_app.models.brand import Brand
from flask import request

def get_current_brand():
    # Extract subdomain (brand1.yourapp.com → brand1)
    host = request.host.split(':')[0]  # remove port if any
    parts = host.split('.')
    if len(parts) > 2:
        subdomain = parts[0]
        brand = Brand.query.filter_by(subdomain=subdomain).first()
        return brand
    return None
