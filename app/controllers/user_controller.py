# app/controllers/user_controller.py

from flask import request, jsonify
from app.extensions import db
from app.models.user import User
from app.services.user_service import UserService
from app.utils.password_helper import hash_password


class UserController:
    @staticmethod
    def create_user():
        data = request.get_json()

        # basic validation
        if not data.get("name") or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Name, email, and password are required"}), 400

        # check if email exists
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 400

        # create new user
        user = User(
            name=data["name"],
            email=data["email"],
            role=data.get("role", "customer"),
            preferences=data.get("preferences", {})
        )
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
