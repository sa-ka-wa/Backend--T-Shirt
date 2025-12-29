from flask import Blueprint, jsonify, request
from backend_app.controllers.user_controller import UserController
from backend_app.utils.jwt_helper import token_required
from backend_app.utils.role_required import role_required

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
@role_required('admin', 'super_admin')
def get_users(current_user, *args, **kwargs):
    print(request.headers)
    return UserController.get_users(current_user)

# Read single user
@user_bp.route("/<int:user_id>", methods=['GET'])
@token_required
@role_required('admin', 'super_admin')
def get_user(current_user):
    return UserController.get_user(current_user)

# Update user
@user_bp.route("/<int:user_id>", methods=['PUT'])
@token_required
def update_user(current_user,user_id):
    return UserController.update_user(current_user,user_id)

# Upload user image (avatar or banner)
@user_bp.route("/<int:user_id>/upload-image", methods=['POST'])
@token_required
def upload_user_image(current_user, user_id):
    return UserController.upload_image(current_user, user_id)


# Delete user
@user_bp.route("/<int:user_id>", methods=['DELETE'])
@token_required
@role_required('admin', 'super_admin')
def delete_user(current_user,user_id):
    return UserController.delete_user(current_user,user_id)
