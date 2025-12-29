# # backend_app/utils/brand_filter.py
# from backend_app.utils.jwt_helper import get_current_user
# from backend_app.models.user import User
#
# def brand_filtered_query(model):
#     """Return query filtered by logged-in user's brand"""
#     user = get_current_user()
#     query = model.query
#     if user.role != "super_admin":
#         query = query.join(User).filter(User.brand_id == user.brand_id)
#     return query
#
#     # Admin → sees only within their brand
#     if user.role == "admin" and user.brand_id:
#         return query.join(User).filter(User.brand_id == user.brand_id)
#
#     # Customer → sees only their own records (if model has user_id)
#     if user.role == "customer" and hasattr(model, "user_id"):
#         return query.filter(model.user_id == user.id)
#
#     return query

# backend_app/utils/brand_filter.py
from backend_app.utils.jwt_helper import get_current_user

def brand_filtered_query(model):
    """Return query filtered by logged-in user's brand"""
    user = get_current_user()
    query = model.query

    # Super admin → sees all
    if user.role == "super_admin":
        return query

    # Admin → filter by brand_id (only their brand’s data)
    if user.role == "admin" and user.brand_id:
        return query.filter(model.brand_id == user.brand_id)

    # Customer → sees only their own records (if model has user_id)
    if user.role == "customer" and hasattr(model, "user_id"):
        return query.filter(model.user_id == user.id)

    # Default
    return query
