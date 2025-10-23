# backend_app/controllers/user_controller.py

from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.user import User
from backend_app.models.brand import Brand
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

        # Determine brand logic
        brand_id = data.get("brand_id")
        brand = None

        if user.role == "super_admin":
            # Super admin can use root brand (1) or provided brand
            user.brand_id = brand_id or 1
            brand = Brand.query.get(user.brand_id)
            if not brand:
                return jsonify({"error": f"Brand with ID {user.brand_id} not found"}), 400
        else:
            if brand_id:
                brand = Brand.query.get(brand_id)
                # ❗ Validate brand existence
                if not brand:
                    return jsonify({"error": f"Brand with ID {brand_id} not found"}), 400
                user.brand_id = brand.id
            else:
                # fallback to subdomain brand
                brand = get_current_brand()
                # ❗ Validate brand existence
                if not brand:
                    return jsonify({"error": "Invalid or missing brand"}), 400
                user.brand_id = brand.id


        # check if email exists within the assigned brand
        if User.query.filter_by(email=user.email, brand_id=user.brand_id).first():
            return jsonify({"error": "Email already exists for this brand"}), 400

        user.set_password(data["password"])  # hashes password

        db.session.add(user)
        db.session.commit()

        # Reload the user and its brand safely
        user = User.query.options(db.joinedload(User.brand)).get(user.id)

        # Build response manually to guarantee correct brand info
        response_data = user.to_dict()

        # If somehow brand_name is still None (e.g., relationship issue), fallback to direct Brand query
        if not response_data.get("brand_name") and user.brand_id:
            brand = Brand.query.get(user.brand_id)
            if brand:
                response_data["brand_name"] = brand.name

        return jsonify({ 
            "message": "User created successfully",
            "user": response_data
        }), 201

    # 🔹 Brand-aware, role-restricted get_users
    @staticmethod
    def get_users(current_user):
        query = User.query

        if current_user.role == "admin":
            query = query.filter_by(brand_id=current_user.brand_id)
        elif current_user.role == "customer":
            return jsonify({"error": "Access denied for customers"}), 403

        users = query.all()
        return jsonify([u.to_dict() for u in users]), 200

    # 🔹 Brand-aware get_user
    @staticmethod
    def get_user(current_user, user_id):
        query = User.query.filter_by(id=user_id)

        if current_user.role == "admin":
            query = query.filter_by(brand_id=current_user.brand_id)

        user = query.first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user.to_dict()), 200

    # 🔹 Allow admins to edit within brand or user editing themselves
    @staticmethod
    def update_user(current_user, user_id):
        data = request.get_json()
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Role-based restrictions
        if current_user.role == "customer" and current_user.id != user_id:
            return jsonify({'error': 'Customers can only update their own account'}), 403
        if current_user.role == "admin" and user.brand_id != current_user.brand_id:
            return jsonify({'error': 'Cannot update user from another brand'}), 403

        for key, value in data.items():
            if key in ["name", "email", "preferences", "role"]:
                setattr(user, key, value)

        db.session.commit()
        return jsonify(user.to_dict()), 200

    # 🔹 Allow delete for admin (same brand) or super_admin (all)
    @staticmethod
    def delete_user(current_user, user_id):
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if current_user.role == "admin" and user.brand_id != current_user.brand_id:
            return jsonify({'error': 'Cannot delete users from another brand'}), 403
        if current_user.role == "customer":
            return jsonify({'error': 'Access denied for customers'}), 403

        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200