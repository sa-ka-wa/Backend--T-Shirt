from flask import Blueprint, request, jsonify
from app.controllers.auth_controller import AuthController
from app.utils.jwt_helper import token_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    return AuthController.register()

@auth_bp.route('/login', methods=['POST'])
def login():
    return AuthController.login()

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    return AuthController.logout()

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    return AuthController.refresh()