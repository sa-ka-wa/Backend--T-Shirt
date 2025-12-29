from backend_app.extensions import db
from backend_app.models.user import User


class UserService:
    @staticmethod
    def get_all_users():
        return User.query.all()

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def update_user(user_id, data):
        user = User.query.get(user_id)
        if not user:
            return None

        # Define allowed fields for update
        allowed_fields = ['name', 'email', 'role', 'preferences', 'bio',
                         'location', 'website', 'phone', 'avatar_url', 'banner_url']

        for key, value in data.items():
            if hasattr(user, key) and key in allowed_fields:
                setattr(user, key, value)

        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return False

        db.session.delete(user)
        db.session.commit()
        return True