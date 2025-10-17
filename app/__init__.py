from flask import Flask
from dotenv import load_dotenv  # ✅ add this
import os                      # ✅ add this
from app.config import Config
from app.extensions import db, jwt, migrate


# ✅ Load .env before Flask reads Config
load_dotenv()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.tshirt_routes import tshirt_bp
    from app.routes.brand_routes import brand_bp
    from app.routes.product_routes import product_bp
    from app.routes.order_routes import order_bp
    from app.routes.payment_routes import payment_bp
    from app.routes.user_routes import user_bp
    from app.routes.style_routes import style_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tshirt_bp, url_prefix='/api/tshirts')
    app.register_blueprint(brand_bp, url_prefix='/api/brands')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(style_bp, url_prefix='/api/themes')

    return app
