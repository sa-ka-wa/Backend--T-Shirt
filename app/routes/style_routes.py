from flask import Blueprint
from app.controllers.style_controller import StyleController
from app.utils.jwt_helper import token_required, admin_required

style_bp = Blueprint('style', __name__)

@style_bp.route('/<style_tag>', methods=['GET'])
def get_theme(style_tag):
    return StyleController.get_theme_by_style_tag(style_tag)

@style_bp.route('/', methods=['GET'])
def get_all_themes():
    return StyleController.get_all_themes()

@style_bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_theme(current_user):
    return StyleController.create_theme()