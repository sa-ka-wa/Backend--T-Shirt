from flask import Flask, send_from_directory
from dotenv import load_dotenv
import os
from backend_app.config import Config
from backend_app.extensions import db, jwt, migrate, cors

# Load .env before Flask config
load_dotenv()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ----------------------------
    # CORS Setup
    # ----------------------------
    # Function to allow dynamic origins (Vercel previews + local dev)
    def allow_origins(origin):
        if origin is None:
            return False
        # Allow any Vercel preview deployment
        if origin.endswith(".vercel.app"):
            return True
        # Allow localhost and lvh.me ports for dev
        allowed = [
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:5173",
            "http://doktari.lvh.me:3002",
            "http://doktari.lvh.me:3003",
            "http://user.lvh.me:3003",
            "http://admin.lvh.me:3001",
            "http://lvh.me:3002",
            "http://lvh.me:3003",
            "http://prolific.lvh.me:3004",
            "https://doktari-frontend.vercel.app",
        ]
        return origin in allowed

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": allow_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                "allow_headers": [
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                    "X-Session-Id",
                ],
                "expose_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
                "max_age": 86400,
            }
        },
    )

    # ----------------------------
    # Initialize Extensions
    # ----------------------------
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # ----------------------------
    # Register Blueprints
    # ----------------------------
    from backend_app.routes.auth_routes import auth_bp
    from backend_app.routes.tshirt_routes import tshirt_bp
    from backend_app.routes.brand_routes import brand_bp
    from backend_app.routes.product_routes import product_bp
    from backend_app.routes.cart_routes import cart_bp
    from backend_app.routes.order_routes import order_bp
    from backend_app.routes.payment_routes import payment_bp
    from backend_app.routes.user_routes import user_bp
    from backend_app.routes.style_routes import style_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tshirt_bp, url_prefix="/api/tshirts")
    app.register_blueprint(brand_bp, url_prefix="/api/brands")
    app.register_blueprint(product_bp, url_prefix="/api/products")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(order_bp, url_prefix="/api/orders")
    app.register_blueprint(payment_bp, url_prefix="/api/payments")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(style_bp, url_prefix="/api/themes")

    # ----------------------------
    # Auto-create DB tables & uploads
    # ----------------------------
    with app.app_context():
        upload_dirs = [
            os.path.join(app.root_path, "static", "uploads", "profiles"),
            os.path.join(app.root_path, "static", "uploads", "products"),
        ]
        for dir_path in upload_dirs:
            os.makedirs(dir_path, exist_ok=True)

        from backend_app import models
        db.create_all()
        print("✅ Database tables created (or already exist)")
        print("✅ Upload directories created")

    # ----------------------------
    # Static file route
    # ----------------------------
    @app.route("/static/uploads/<path:filename>")
    def serve_uploaded_files(filename):
        return send_from_directory(
            os.path.join(app.root_path, "static", "uploads"), filename
        )

    # ----------------------------
    # List all routes (debug)
    # ----------------------------
    @app.route("/routes", methods=["GET"])
    def list_routes():
        output = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != "static":
                output.append(
                    {"endpoint": rule.endpoint, "methods": ",".join(rule.methods), "url": str(rule)}
                )
        return {"routes": output}, 200

    return app
