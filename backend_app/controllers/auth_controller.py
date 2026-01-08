from flask import request, jsonify, redirect, url_for
from backend_app.extensions import db
from backend_app.models.user import User
from backend_app.models.brand import Brand
from backend_app.controllers.user_controller import UserController
from backend_app.services.auth_service import AuthService
from backend_app.utils.jwt_helper import get_jwt_identity, generate_token
import requests
from oauthlib.oauth2 import WebApplicationClient
import os
import json
import uuid

# Ensure oauthlib will allow HTTP in development (useful for local testing)
# Accept either FLASK_ENV=development or explicit OAUTHLIB_INSECURE_TRANSPORT in env/.env
if os.environ.get("FLASK_ENV", "").lower() == "development" or os.environ.get("OAUTHLIB_INSECURE_TRANSPORT") == "1":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


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
        """
        Redirects the user to Google's OAuth consent screen.
        Optionally accepts ?redirect_to=<frontend URL> to send user after login.
        """
        google_provider_cfg = requests.get(AuthController.GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        redirect_uri = url_for("auth.google_callback", _external=True)
        request_uri = AuthController.client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)

    @staticmethod
    def google_auth_callback():
        """
        Handles the callback from Google after login.
        Uses query parameters instead of hash fragments for better compatibility.
        """
        try:
            code = request.args.get("code")
            if not code:
                return {"error": "Authorization code missing"}, 400

            # Fetch Google endpoints
            google_provider_cfg = requests.get(AuthController.GOOGLE_DISCOVERY_URL).json()
            token_endpoint = google_provider_cfg["token_endpoint"]
            userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]

            # Same redirect URI used for both auth and token
            redirect_uri = url_for("auth.google_callback", _external=True)

            # Exchange code for tokens
            token_data = {
                "code": code,
                "client_id": AuthController.GOOGLE_CLIENT_ID,
                "client_secret": AuthController.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
            token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
            token_response = requests.post(token_endpoint, data=token_data, headers=token_headers)
            if token_response.status_code != 200:
                return {"error": "Failed to exchange code for token", "details": token_response.json()}, 400

            tokens = token_response.json()
            access_token = tokens.get("access_token")
            if not access_token:
                return {"error": "No access_token received", "details": tokens}, 400

            # Fetch user info
            userinfo_response = requests.get(userinfo_endpoint, headers={"Authorization": f"Bearer {access_token}"})
            if userinfo_response.status_code != 200:
                return {"error": "Failed to get user info", "details": userinfo_response.text}, 400

            userinfo = userinfo_response.json()
            email = userinfo["email"]
            name = userinfo.get("given_name", email.split("@")[0])

            # Create or get user
            user = User.query.filter_by(email=email).first()
            if not user:
                brand = Brand.query.first()  # fallback brand
                user = User(
                    email=email,
                    name=name,
                    role="customer",
                    brand_id=brand.id if brand else None
                )
                # Random password for Google users
                user.set_password(uuid.uuid4().hex)
                db.session.add(user)
                db.session.commit()

            # Generate JWT - IMPORTANT: Convert user.id to string
            user_id_str = str(user.id)
            token = generate_token(user_id_str)

            # ✅ CRITICAL FIX: Use query parameters instead of hash fragment
            # This works better with Vercel/React Router
            frontend_url = os.environ.get("FRONTEND_URL", "https://doktari-frontend.vercel.app")

            # Use query parameters for better compatibility
            target = f"{frontend_url.rstrip('/')}/auth/callback?token={token}"

            # Add cache control headers
            response = redirect(target)
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'

            print(f"✅ Google OAuth successful for user: {email}")
            print(f"✅ Redirecting to: {target}")

            return response

        except Exception as e:
            print(f"❌ Google authentication failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"Google authentication failed: {str(e)}"}, 400