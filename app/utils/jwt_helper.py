from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from functools import wraps
from flask import jsonify
from app.models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()  # Just check validity — don't pass user
        except Exception as e:
            print("JWT error:", e)
            return jsonify({'error': 'Valid JWT token is missing'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            user_id = get_jwt_identity()
            current_user = User.query.get(user_id)

            if not current_user:
                return jsonify({'error': 'User not found'}), 404

            if not claims.get('is_admin', False):
                return jsonify({'error': 'Admin privileges required'}), 403

        except Exception as e:
            print("JWT error:", e)
            return jsonify({'error': 'Valid JWT token is missing'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def get_current_user_id():
    """
    Extracts the current user's ID from the JWT token.
    Returns None if the token is invalid or missing.
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        return user_id
    except Exception as e:
        print("JWT Error:", e)
        return None