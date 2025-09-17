from flask import Flask
from app.config import Config
from app.extensions import db, jwt, migrate


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
    from app.routes.order_routes import order_bp
    from app.routes.payment_routes import payment_bp
    from app.routes.user_routes import user_bp
    from app.routes.style_routes import style_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tshirt_bp, url_prefix='/api/tshirts')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(style_bp, url_prefix='/api/themes')

    return app