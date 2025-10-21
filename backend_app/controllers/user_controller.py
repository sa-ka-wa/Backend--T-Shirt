# backend_app/controllers/user_controller.py

from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.user import User
from backend_app.services.user_service import UserService
from backend_app.utils.password_helper import hash_password
from backend_app.utils.brand_helper import get_current_brand


class UserController:
    @staticmethod
    def create_user():
        data = request.get_json()

        # basic validation
        if not data.get("name") or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Name, email, and password are required"}), 400

        # create new user
        user = User(
            name=data["name"],
            email=data["email"],
            role=data.get("role", "customer"),
            preferences=data.get("preferences", {})
        )

        # get brand from subdomain only if needed
        brand = get_current_brand()

        # Assign brand
        brand_id = data.get("brand_id")  # check JSON first
        if user.role == "super_admin":
            # Super admin can use root brand (1) or provided brand
            user.brand_id = brand_id or 1
        else:
            if brand_id:
                user.brand_id = brand_id
            else:
                # fallback to subdomain brand
                brand = get_current_brand()
                if not brand:
                    return jsonify({"error": "Invalid or missing brand"}), 400
                user.brand_id = brand.id

        # check if email exists within the assigned brand
        if User.query.filter_by(email=user.email, brand_id=user.brand_id).first():
            return jsonify({"error": "Email already exists for this brand"}), 400

        user.set_password(data["password"])  # hashes password

        db.session.add(user)
        db.session.commit()

        return jsonify(user.to_dict()), 201

    @staticmethod
    def get_users():
        users = UserService.get_all_users()
        return jsonify([user.to_dict() for user in users])

    @staticmethod
    def get_user(user_id):
        user = UserService.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())

    @staticmethod
    def update_user(user_id):
        data = request.get_json()
        user = UserService.update_user(user_id, data)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())

    @staticmethod
    def delete_user(user_id):
        success = UserService.delete_user(user_id)
        if not success:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'message': 'User deleted successfully'}), 200
