from flask import Blueprint, request, jsonify
from backend_app.controllers.auth_controller import AuthController
from backend_app.models.user import User
from backend_app.utils.jwt_helper import token_required,get_jwt_identity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    return AuthController.register()

@auth_bp.route('/login', methods=['POST'])
def login():
    return AuthController.login()

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    return AuthController.logout()

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    return AuthController.refresh()

# ✅ NEW: Get current user (used by frontend)
@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    return AuthController.get_current_user()


# ✅ NEW: Google OAuth Routes
@auth_bp.route('/google', methods=['GET'])
def google_login():
    return AuthController.google_login()

@auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    return AuthController.google_auth_callback()

@auth_bp.route('/profile', methods=['GET'])
@token_required
def profile(current_user):  # <-- accept injected user
    return AuthController.get_current_user(current_user)

