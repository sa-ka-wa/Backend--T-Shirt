from app.extensions import db
from app.models.user import User
from app.utils.password_helper import hash_password, verify_password
from flask_jwt_extended import create_access_token


class AuthService:
    @staticmethod
    def register_user(email, password, name, role='customer'):
        user = User(
            email=email,
            name=name,
            role=role
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def login_user(email, password):
        user = User.query.filter_by(email=email).first()

        if not user or not verify_password(user.password_hash, password):
            return {'error': 'Invalid email or password'}

        # Create access token
        access_token = create_access_token(
            identity=str(user.id),  # Convert user.id to string
            additional_claims={'is_admin': user.role == 'admin'}
        )

        return {
            'access_token': access_token,
            'user': user.to_dict()
        }