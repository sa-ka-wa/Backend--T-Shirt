import os
from backend_app.extensions import db
from backend_app.models.brand import Brand
from backend_app.models.user import User
from backend_app.utils.password_helper import hash_password
from app import create_app

app = create_app()

if os.getenv("FLASK_ENV") == "production":
    print("⚠️ Seeding disabled in production mode for safety.")
    exit()

with app.app_context():
    brand = Brand.query.filter_by(name="Default Brand").first()
    if not brand:
        brand = Brand(name="Default Brand")
        db.session.add(brand)
        db.session.commit()
        print("✅ Default brand added.")

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name="Admin",
            email=admin_email,
            password_hash=hash_password(admin_password),
            role="admin",
            brand_id=brand.id
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin user added: {admin_email}")

