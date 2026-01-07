import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_app import create_app
from backend_app.extensions import db
from backend_app.models.user import User
from backend_app.models.brand import Brand
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app()


def create_brand_users():
    with app.app_context():
        print("=== Creating Brand Admin and Staff Users ===")

        # Get existing brands
        brands = Brand.query.all()
        print(f"Found {len(brands)} brands:")
        for brand in brands:
            print(f"  - ID: {brand.id}, Name: {brand.name}")

        # Create brand_admin and brand_staff for each brand
        users_to_create = []

        for brand in brands:
            # Brand Admin
            brand_admin_email = f"{brand.name.lower().replace(' ', '')}.admin@example.com"
            users_to_create.append({
                'name': f'{brand.name} Admin',
                'email': brand_admin_email,
                'password': 'password123',
                'role': 'brand_admin',
                'brand_id': brand.id
            })

            # Brand Staff (multiple per brand)
            for i in range(1, 4):
                staff_email = f"{brand.name.lower().replace(' ', '')}.staff{i}@example.com"
                users_to_create.append({
                    'name': f'{brand.name} Staff {i}',
                    'email': staff_email,
                    'password': 'password123',
                    'role': 'brand_staff',
                    'brand_id': brand.id
                })

        created_count = 0
        for user_data in users_to_create:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()

            if existing_user:
                print(f"User {user_data['email']} already exists")
                # Update role if needed
                if existing_user.role != user_data['role']:
                    existing_user.role = user_data['role']
                    existing_user.brand_id = user_data['brand_id']
                    db.session.commit()
                    print(f"  Updated role to {user_data['role']}")
            else:
                try:
                    user = User(
                        name=user_data['name'],
                        email=user_data['email'],
                        password_hash=generate_password_hash(user_data['password']),
                        role=user_data['role'],
                        brand_id=user_data['brand_id'],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(user)
                    db.session.commit()
                    created_count += 1
                    print(f"Created user: {user_data['email']} ({user_data['role']}) for brand {user_data['brand_id']}")
                except Exception as e:
                    print(f"Error creating user {user_data['email']}: {e}")
                    db.session.rollback()

        print(f"\n✅ Created/updated {created_count} brand users")

        # Display all users with brand roles
        print("\n=== Brand Admin/Staff Users ===")
        brand_users = User.query.filter(User.role.in_(['brand_admin', 'brand_staff'])).all()

        for user in brand_users:
            brand_name = user.brand.name if user.brand else 'No Brand'
            print(f"{user.email:<40} {user.role:<15} {brand_name:<20}")


def create_postman_test_users():
    """Create specific users for Postman testing"""
    with app.app_context():
        print("\n=== Creating Postman Test Users ===")

        # Define test users for different scenarios
        test_users = [
            # Brand Admin for Nike
            {
                'name': 'Nike Brand Admin',
                'email': 'nike.brandadmin@postman.com',
                'password': 'password123',
                'role': 'brand_admin',
                'brand_id': 1,  # Nike Updated
                'purpose': 'Test brand admin permissions for Nike'
            },
            # Brand Staff for Nike
            {
                'name': 'Nike Staff 1',
                'email': 'nike.staff1@postman.com',
                'password': 'password123',
                'role': 'brand_staff',
                'brand_id': 1,
                'purpose': 'Test brand staff permissions'
            },
            # Brand Admin for Adidas
            {
                'name': 'Adidas Brand Admin',
                'email': 'adidas.brandadmin@postman.com',
                'password': 'password123',
                'role': 'brand_admin',
                'brand_id': 3,  # Adidas
                'purpose': 'Test brand admin for Adidas'
            },
            # Customer for Nike
            {
                'name': 'Nike Customer',
                'email': 'nike.customer@postman.com',
                'password': 'password123',
                'role': 'customer',
                'brand_id': 1,
                'purpose': 'Test customer orders'
            },
            # Customer for Adidas
            {
                'name': 'Adidas Customer',
                'email': 'adidas.customer@postman.com',
                'password': 'password123',
                'role': 'customer',
                'brand_id': 3,
                'purpose': 'Test customer from different brand'
            },
            # Platform Admin (for comparison)
            {
                'name': 'Platform Admin',
                'email': 'platform.admin@postman.com',
                'password': 'password123',
                'role': 'admin',
                'brand_id': None,
                'purpose': 'Test platform-wide admin'
            }
        ]

        created_count = 0
        for user_data in test_users:
            existing_user = User.query.filter_by(email=user_data['email']).first()

            if existing_user:
                print(f"User {user_data['email']} already exists - updating")
                existing_user.name = user_data['name']
                existing_user.role = user_data['role']
                existing_user.brand_id = user_data['brand_id']
                db.session.commit()
            else:
                try:
                    user = User(
                        name=user_data['name'],
                        email=user_data['email'],
                        password_hash=generate_password_hash(user_data['password']),
                        role=user_data['role'],
                        brand_id=user_data['brand_id'],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(user)
                    db.session.commit()
                    created_count += 1
                    print(f"Created: {user_data['email']} ({user_data['role']}) - {user_data['purpose']}")
                except Exception as e:
                    print(f"Error creating {user_data['email']}: {e}")
                    db.session.rollback()

        print(f"\n✅ Created/updated {created_count} Postman test users")

        # Display all test users
        print("\n=== Postman Test Users ===")
        postman_users = User.query.filter(User.email.like('%@postman.com')).all()

        print("\nEmail                     | Role           | Brand           | Purpose")
        print("-" * 80)
        for user in postman_users:
            brand_name = user.brand.name if user.brand else 'Platform'
            purpose = next((u['purpose'] for u in test_users if u['email'] == user.email), 'Test user')
            print(f"{user.email:<25} {user.role:<15} {brand_name:<15} {purpose}")


def export_users_for_postman():
    """Export users in a format easy to copy into Postman"""
    with app.app_context():
        print("\n=== Users for Postman Collection ===")

        # Get all users
        users = User.query.all()

        print("\nCopy the following JSON into Postman:")
        print("[")

        for i, user in enumerate(users):
            user_dict = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "brand_id": user.brand_id,
                "brand_name": user.brand.name if user.brand else None,
                "password": "password123"  # Default password for all test users
            }

            # Print as JSON
            import json
            user_json = json.dumps(user_dict, indent=2)
            if i < len(users) - 1:
                print(user_json + ",")
            else:
                print(user_json)

        print("]")

        # Also print as a table
        print("\n=== Quick Reference Table ===")
        print("\nEmail                     | Password    | Role           | Brand")
        print("-" * 80)

        for user in users:
            brand_name = user.brand.name if user.brand else 'None'
            print(f"{user.email:<25} password123  {user.role:<15} {brand_name}")


if __name__ == '__main__':
    print("Creating brand admin and staff users...\n")

    create_brand_users()
    create_postman_test_users()
    export_users_for_postman()