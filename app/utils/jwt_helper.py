from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps
from flask import jsonify

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except:
            return jsonify({'error': 'Valid JWT token is missing'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims.get('is_admin', False):
                return jsonify({'error': 'Admin privileges required'}), 403
        except:
            return jsonify({'error': 'Valid JWT token is missing'}), 401
        return f(*args, **kwargs)
    return decorated