# backend_app/utils/brand_filter.py
from backend_app.utils.jwt_helper import get_current_user
from backend_app.models.user import User

def brand_filtered_query(model):
    """Return query filtered by logged-in user's brand"""
    user = get_current_user()
    query = model.query
    if user.role != "super_admin":
        query = query.join(User).filter(User.brand_id == user.brand_id)
    return query
