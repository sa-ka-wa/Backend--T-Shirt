from flask import request, jsonify
from backend_app.extensions import db
from backend_app.models.user import User
from backend_app.controllers.user_controller import UserController
from backend_app.services.auth_service import AuthService


class AuthController:
    @staticmethod
    # def register():
    #     data = request.get_json()
    #
    #     # Validate required fields
    #     if not data.get('email') or not data.get('password') or not data.get('name'):
    #         return jsonify({'error': 'Email, password, and name are required'}), 400
    #
    #     # Check if user already exists
    #     if User.query.filter_by(email=data['email']).first():
    #         return jsonify({'error': 'User already exists'}), 409
    #
    #     # Create new user
    #     user = AuthService.register_user(
    #         data['email'],
    #         data['password'],
    #         data['name'],
    #         data.get('role', 'customer')
    #     )
    #
    #     return jsonify({
    #         'message': 'User created successfully',
    #         'user': user.to_dict()
    #     }), 201

    def register():
        # ✅ Reuse the brand-safe user creation logic
        return UserController.create_user()

    @staticmethod
    def login():
        data = request.get_json()

        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        result = AuthService.login_user(data['email'], data['password'])

        if 'error' in result:
            return jsonify({'error': result['error']}), 401

        return jsonify(result), 200

    @staticmethod
    def logout():
        # JWT tokens are stateless, so logout is handled on the client side
        return jsonify({'message': 'Successfully logged out'}), 200

    @staticmethod
    def refresh():
        # Refresh token logic would go here
        return jsonify({'message': 'Token refresh endpoint'}), 200