from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt, create_access_token
from functools import wraps
from flask import jsonify, request
from backend_app.models.user import User


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Handle OPTIONS preflight requests
        if request.method == 'OPTIONS':
            return f(None, *args, **kwargs)

        try:
            # Verify the JWT token using flask_jwt_extended
            verify_jwt_in_request()
            user_id = get_jwt_identity()

            if not user_id:
                return jsonify({'error': 'Token is invalid'}), 401

            current_user = User.query.get(user_id)

            if not current_user:
                return jsonify({'error': 'User not found'}), 404

            return f(current_user, *args, **kwargs)

        except Exception as e:
            print("JWT Verification Error:", e)
            return jsonify({'error': 'Token is invalid or expired'}), 401

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Handle OPTIONS preflight requests
        if request.method == 'OPTIONS':
            return f(None, *args, **kwargs)

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


def get_current_user():
    """
    Returns the full User object of the currently authenticated user.
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        if not user_id:
            return None
        user = User.query.get(user_id)
        return user
    except Exception as e:
        print("JWT Error:", e)
        return None


def generate_token(identity, additional_claims=None):
    """
    Generates a JWT access token for the given user identity.
    Includes custom claims if provided.
    """
    if additional_claims is None:
        additional_claims = {}

    # ✅ CRITICAL FIX: Ensure identity is a string
    if not isinstance(identity, str):
        identity = str(identity)

    return create_access_token(identity=identity, additional_claims=additional_claims)

# Optional: Add a specific decorator for cart endpoints that handles both authenticated and guest users
def cart_token_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = None

        # Try to get user from token, but don't fail if not present
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                current_user = User.query.get(user_id)
        except:
            # Token is invalid or expired, treat as guest
            current_user = None

        # Pass current_user (could be None for guests)
        return f(current_user, *args, **kwargs)

    return decorated