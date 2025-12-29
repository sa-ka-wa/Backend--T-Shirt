# fix_data.py
from backend_app import create_app
from backend_app.extensions import db
from backend_app.models.user import User
from backend_app.models.brand import Brand

app = create_app()

with app.app_context():
    print("=== Fixing NULL brand_id values ===")

    # Check for users with NULL brand_id
    null_brand_users = User.query.filter(User.brand_id.is_(None)).all()
    print(f"Found {len(null_brand_users)} users with NULL brand_id")

    # Get or create a default brand
    default_brand = Brand.query.first()
    if not default_brand:
        print("No brands found, creating a default brand...")
        default_brand = Brand(name="Default Brand", subdomain="default")
        db.session.add(default_brand)
        db.session.commit()
        print(f"Created default brand with ID: {default_brand.id}")
    else:
        print(f"Using existing brand: {default_brand.name} (ID: {default_brand.id})")

    # Update users with NULL brand_id
    if null_brand_users:
        for user in null_brand_users:
            print(f"Updating user {user.id} ({user.name}) - setting brand_id to {default_brand.id}")
            user.brand_id = default_brand.id

        db.session.commit()
        print("✅ All users updated successfully!")
    else:
        print("✅ No users with NULL brand_id found!")

    # Verify the fix
    remaining_null_users = User.query.filter(User.brand_id.is_(None)).all()
    print(f"Remaining users with NULL brand_id: {len(remaining_null_users)}")