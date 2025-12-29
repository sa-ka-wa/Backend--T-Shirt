from flask import request, jsonify, redirect
from backend_app.extensions import db
from backend_app.models.user import User
from backend_app.controllers.user_controller import UserController
from backend_app.services.auth_service import AuthService
from backend_app.utils.jwt_helper import get_jwt_identity, generate_token
import requests
from oauthlib.oauth2 import WebApplicationClient
import os
import json


class AuthController:
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-google-client-id")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    client = WebApplicationClient(GOOGLE_CLIENT_ID)

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

    @staticmethod
    def get_current_user(user):

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user.to_dict()), 200

    # ✅ NEW: Google OAuth Login
    @staticmethod
    def google_login():
        try:
            # Get Google's OAuth 2.0 endpoints
            google_provider_cfg = requests.get(AuthController.GOOGLE_DISCOVERY_URL).json()
            authorization_endpoint = google_provider_cfg["authorization_endpoint"]

            # Prepare request URI
            request_uri = AuthController.client.prepare_request_uri(
                authorization_endpoint,
                redirect_uri=request.host_url + "api/auth/google/callback",
                scope=["openid", "email", "profile"],
            )
            return redirect(request_uri)
        except Exception as e:
            return jsonify({"error": f"Google OAuth configuration failed: {str(e)}"}), 500

    # ✅ NEW: Google OAuth Callback
    @staticmethod
    def google_auth_callback():
        try:
            # Get authorization code Google sent back
            code = request.args.get("code")

            if not code:
                return jsonify({"error": "Authorization code missing"}), 400

            # Exchange code for tokens
            google_provider_cfg = requests.get(AuthController.GOOGLE_DISCOVERY_URL).json()
            token_endpoint = google_provider_cfg["token_endpoint"]

            token_url, headers, body = AuthController.client.prepare_token_request(
                token_endpoint,
                authorization_response=request.url,
                redirect_url=request.base_url,
                code=code
            )

            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(AuthController.GOOGLE_CLIENT_ID, AuthController.GOOGLE_CLIENT_SECRET),
            )

            if token_response.status_code != 200:
                return jsonify({"error": "Failed to get tokens from Google"}), 400

            # Parse the tokens
            AuthController.client.parse_request_body_response(token_response.text)

            # Get user info from Google
            userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
            uri, headers, body = AuthController.client.add_token(userinfo_endpoint)
            userinfo_response = requests.get(uri, headers=headers, data=body)

            if userinfo_response.status_code != 200:
                return jsonify({"error": "Failed to get user info from Google"}), 400

            userinfo = userinfo_response.json()

            if userinfo.get("email_verified"):
                users_email = userinfo["email"]
                users_name = userinfo.get("given_name", users_email.split('@')[0])

                # Create or get user from database
                user = User.query.filter_by(email=users_email).first()
                if not user:
                    user = User(
                        email=users_email,
                        username=users_name,
                        password_hash=None,  # Google users don't need password
                        role='customer'
                    )
                    db.session.add(user)
                    db.session.commit()

                # Generate JWT token
                token = generate_token(user.id)
                return jsonify({
                    "message": "Google login successful",
                    "token": token,
                    "user": user.to_dict()
                }), 200
            else:
                return jsonify({"error": "Google email not verified"}), 400

        except Exception as e:
            return jsonify({"error": f"Google authentication failed: {str(e)}"}), 400