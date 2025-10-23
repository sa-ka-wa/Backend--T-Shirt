from functools import wraps
from flask import jsonify
from backend_app.utils.jwt_helper import get_current_user

def role_required(*roles):
    """
    Decorator to restrict access to specific roles.
    Example: @role_required('admin', 'super_admin')
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify({'error': 'Unauthorized'}), 401

            if user.role not in roles:
                return jsonify({'error': f'Access denied for role: {user.role}'}), 403

            return f(user,*args, **kwargs)
        return wrapper
    return decorator
