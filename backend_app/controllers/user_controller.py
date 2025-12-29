# backend_app/controllers/user_controller.py

from flask import request, jsonify, current_app
from backend_app.extensions import db
from backend_app.models.user import User
from backend_app.models.brand import Brand
from backend_app.services.user_service import UserService
from backend_app.utils.password_helper import hash_password
from backend_app.utils.brand_helper import get_current_brand
import os
import uuid


class UserController:
    @staticmethod
    def create_user():
        data = request.get_json()

        # basic validation
        if not data.get("name") or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Name, email, and password are required"}), 400

        # STEP 1 — Detect brand from subdomain
        brand_id = data.get("brand_id")
        brand = Brand.query.get(brand_id)
        if not brand:
            return jsonify({"error": "Brand not found"}), 400

        # create new user
        user = User(
            name=data["name"],
            email=data["email"],
            role=data.get("role", "customer"),
            preferences=data.get("preferences", {}),
            # New fields
            bio=data.get("bio"),
            location=data.get("location"),
            website=data.get("website"),
            phone=data.get("phone"),
            brand_id=brand.id
        )

        # STEP 3 — Block duplicate emails *per brand*
        if User.query.filter_by(email=user.email, brand_id=brand.id).first():
            return jsonify({"error": "Email already exists for this brand"}), 400

        # STEP 4 — Hash password
        user.set_password(data["password"])

        # STEP 5 — Save user
        db.session.add(user)
        db.session.commit()

        # Reload with brand relationship
        user = User.query.options(db.joinedload(User.brand)).get(user.id)
        response_data = user.to_dict()

        # Fix missing brand_name (just in case)
        if not response_data.get("brand_name"):
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

        # Update allowed fields
        allowed_fields = ["name", "email", "preferences", "role", "bio", "location", "website", "phone"]

        for key, value in data.items():
            if key in allowed_fields:
                setattr(user, key, value)

        db.session.commit()
        return jsonify(user.to_dict()), 200

    @staticmethod
    def upload_image(current_user, user_id):
        """Handle avatar and banner image uploads"""
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate user permissions
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if current_user.role == "customer" and current_user.id != user_id:
            return jsonify({'error': 'Can only upload images for your own profile'}), 403
        if current_user.role == "admin" and user.brand_id != current_user.brand_id:
            return jsonify({'error': 'Cannot upload images for users from another brand'}), 403

        # Get upload type (avatar or banner)
        upload_type = request.form.get('type', 'avatar')
        if upload_type not in ['avatar', 'banner']:
            return jsonify({'error': 'Invalid upload type'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': 'Invalid file type'}), 400

        try:
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{upload_type}_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"

            # Create upload directory if it doesn't exist
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
            os.makedirs(upload_folder, exist_ok=True)

            # Save file
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)

            # Generate URL for the saved file
            image_url = f"/static/uploads/profiles/{unique_filename}"

            # Update user record
            if upload_type == 'avatar':
                user.avatar_url = image_url
            else:
                user.banner_url = image_url

            db.session.commit()

            return jsonify({
                'message': f'{upload_type.capitalize()} image uploaded successfully',
                'imageUrl': image_url
            }), 200

        except Exception as e:
            current_app.logger.error(f"Error uploading image: {str(e)}")
            return jsonify({'error': 'Failed to upload image'}), 500


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