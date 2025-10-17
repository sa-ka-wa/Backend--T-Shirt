from flask import Blueprint, jsonify, request
from app.controllers.user_controller import UserController
from app.utils.jwt_helper import token_required

# Add a URL prefix so routes are properly namespaced
user_bp = Blueprint('users', __name__, url_prefix="/api/users")

# Create (Register a new user) → no token needed
@user_bp.route("", methods=['POST'])
def create_user():
    print(request.headers)
    return UserController.create_user()

# Read all users (requires token)
@user_bp.route("", methods=['GET'])
@token_required
def get_users():
    print(request.headers)
    return UserController.get_users()

# Read single user
@user_bp.route("/<int:user_id>", methods=['GET'])
@token_required
def get_user(user_id):
    return UserController.get_user(user_id)

# Update user
@user_bp.route("/<int:user_id>", methods=['PUT'])
@token_required
def update_user(user_id):
    return UserController.update_user(user_id)

# Delete user
@user_bp.route("/<int:user_id>", methods=['DELETE'])
@token_required
def delete_user(user_id):
    return UserController.delete_user(user_id)
