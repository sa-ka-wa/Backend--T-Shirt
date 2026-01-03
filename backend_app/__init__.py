from flask import Flask,send_from_directory
from dotenv import load_dotenv  # ✅ add this
import os                      # ✅ add this
from backend_app.config import Config
from backend_app.extensions import db, jwt, migrate, cors

# ✅ Load .env before Flask reads Config
load_dotenv()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ⚠️ CRITICAL FIX: Handle CORS properly
    # Allow credentials and handle OPTIONS requests
    app.config['CORS_SUPPORTS_CREDENTIALS'] = True
    app.config['CORS_HEADERS'] = ['Content-Type', 'Authorization', 'X-Requested-With']

    # ✅ Initialize CORS with proper settings
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://prolific.lvh.me:3004",
                "http://lvh.me:3003",
                "http://doktari.lvh.me:3002",
            "https://doktari-frontend.vercel.app",
                "http://admin.lvh.me:3001",
                "http://user.lvh.me:3003",
                "http://localhost:3001",
                "http://localhost:3002",
                "http://localhost:3003",
                "http://localhost:5173",
                "http://*.lvh.me:3002",
                "http://lvh.me:3002"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "X-Session-Id"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 86400  # Cache preflight for 24 hours
        }
    })

    # ⚠️ IMPORTANT: Add this to handle preflight OPTIONS requests
    # @app.after_request
    # def after_request(response):
    #     # Add CORS headers to all responses
    #     response.headers.add('Access-Control-Allow-Origin',
    #                          'http://doktari.lvh.me:3002')  # Or use your frontend origin
    #     response.headers.add('Access-Control-Allow-Headers',
    #                          'Content-Type,Authorization,X-Requested-With')
    #     response.headers.add('Access-Control-Allow-Methods',
    #                          'GET,PUT,POST,DELETE,OPTIONS')
    #     response.headers.add('Access-Control-Allow-Credentials', 'true')
    #     return response

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from backend_app.routes.auth_routes import auth_bp
    from backend_app.routes.tshirt_routes import tshirt_bp
    from backend_app.routes.brand_routes import brand_bp
    from backend_app.routes.product_routes import product_bp
    from backend_app.routes.cart_routes import cart_bp
    from backend_app.routes.order_routes import order_bp
    from backend_app.routes.payment_routes import payment_bp
    from backend_app.routes.user_routes import user_bp
    from backend_app.routes.style_routes import style_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tshirt_bp, url_prefix='/api/tshirts')
    app.register_blueprint(brand_bp, url_prefix='/api/brands')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(style_bp, url_prefix='/api/themes')

    # ✅ Auto-create tables if they don't exist
    with app.app_context():
        # Create necessary upload directories
        upload_dirs = [
            os.path.join(app.root_path, 'static', 'uploads', 'profiles'),
            os.path.join(app.root_path, 'static', 'uploads', 'products'),
            # Add other upload directories as needed
        ]

        for upload_dir in upload_dirs:
            os.makedirs(upload_dir, exist_ok=True)

        # Create database tables
        from backend_app import models
        db.create_all()
        print("✅ Database tables created (or already exist)")
        print("✅ Upload directories created")

    # ✅ Static file route for uploaded images
    @app.route('/static/uploads/<path:filename>')
    def serve_uploaded_files(filename):
        """Serve uploaded files like profile images"""
        return send_from_directory(os.path.join(app.root_path, 'static', 'uploads'), filename)

    @app.route("/routes", methods=["GET"])
    def list_routes():
        """
        Lists all active routes in the Flask app.
        """
        output = []
        for rule in app.url_map.iter_rules():
            # Skip static routes unless you want them
            if rule.endpoint != 'static':
                methods = ",".join(rule.methods)
                output.append({
                    "endpoint": rule.endpoint,
                    "methods": methods,
                    "url": str(rule)
                })
        return {"routes": output}, 200


    return app
