import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_app import create_app
from backend_app.extensions import db
from sqlalchemy import text
from datetime import datetime
import random
import json

app = create_app()


def fix_database_schema():
    with app.app_context():
        connection = db.engine.connect()
        trans = connection.begin()

        try:
            print("=== Complete Database Schema Fix ===")

            # 1. First, make product_title and product_price nullable in order_items
            print("\n1. Making order_items columns nullable...")

            # Check constraints
            result = connection.execute(text("""
                SELECT tc.table_name, kcu.column_name, tc.constraint_type
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'order_items' 
                AND tc.constraint_type = 'CHECK'
            """))

            # Drop NOT NULL constraints if they exist
            for column in ['product_title', 'product_price']:
                try:
                    # First try to make them nullable
                    connection.execute(text(f"""
                        ALTER TABLE order_items 
                        ALTER COLUMN {column} DROP NOT NULL
                    """))
                    print(f"   Made {column} nullable")
                except:
                    print(f"   {column} is already nullable or doesn't exist")

            # 2. Add missing columns to order_items
            print("\n2. Adding missing columns to order_items...")

            order_items_columns = [
                ('unit_price', 'FLOAT'),
                ('customization_data', 'JSONB')
            ]

            for column_name, column_type in order_items_columns:
                # Check if column exists
                result = connection.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'order_items' AND column_name = '{column_name}'
                """))

                if not result.fetchone():
                    print(f"   Adding {column_name}...")
                    connection.execute(text(f"ALTER TABLE order_items ADD COLUMN {column_name} {column_type}"))

            # 3. Migrate data from orders to order_items
            print("\n3. Migrating data from orders to order_items...")

            # Get orders that need migration (those with product_id in orders table)
            result = connection.execute(text("""
                SELECT o.id as order_id, o.user_id, o.product_id, o.quantity, 
                       o.total_amount, o.created_at, o.status,
                       p.title as product_title, p.price as product_price
                FROM orders o
                LEFT JOIN products p ON o.product_id = p.id
                WHERE o.product_id IS NOT NULL 
                AND NOT EXISTS (
                    SELECT 1 FROM order_items oi 
                    WHERE oi.order_id = o.id
                )
            """))

            orders_to_migrate = result.fetchall()
            migrated_count = 0

            for order in orders_to_migrate:
                (order_id, user_id, product_id, quantity, total_amount,
                 created_at, status, product_title, product_price) = order

                # Calculate unit price
                if product_price:
                    unit_price = product_price
                elif quantity > 0:
                    unit_price = total_amount / quantity
                else:
                    unit_price = 0

                # Insert into order_items
                connection.execute(text("""
                    INSERT INTO order_items 
                    (order_id, product_id, product_title, product_price, 
                     quantity, total_price, unit_price, created_at)
                    VALUES (:order_id, :product_id, :product_title, :product_price,
                            :quantity, :total_price, :unit_price, :created_at)
                """), {
                    'order_id': order_id,
                    'product_id': product_id,
                    'product_title': product_title or f'Product {product_id}',
                    'product_price': product_price or unit_price,
                    'quantity': quantity,
                    'total_price': total_amount,
                    'unit_price': unit_price,
                    'created_at': created_at or datetime.utcnow()
                })
                migrated_count += 1

            print(f"   Migrated {migrated_count} orders to order_items")

            # 4. Add missing columns to orders table
            print("\n4. Adding columns to orders table...")

            orders_columns = [
                ('order_number', 'VARCHAR(50)'),
                ('subtotal', 'FLOAT'),
                ('tax_amount', 'FLOAT DEFAULT 0.0'),
                ('shipping_amount', 'FLOAT DEFAULT 0.0'),
                ('billing_address', 'JSONB'),
                ('notes', 'TEXT'),
                ('tracking_number', 'VARCHAR(100)'),
                ('carrier', 'VARCHAR(100)'),
                ('estimated_delivery', 'TIMESTAMP'),
                ('delivered_at', 'TIMESTAMP'),
                ('cancelled_at', 'TIMESTAMP'),
                ('cancellation_reason', 'TEXT'),
                ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            ]

            for column_name, column_type in orders_columns:
                # Check if column exists
                result = connection.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'orders' AND column_name = '{column_name}'
                """))

                if not result.fetchone():
                    print(f"   Adding {column_name}...")
                    # Add as nullable first
                    if 'DEFAULT' in column_type:
                        col_def = column_type
                    else:
                        col_def = f"{column_type}"

                    connection.execute(text(f"ALTER TABLE orders ADD COLUMN {column_name} {col_def}"))

            # 5. Generate order numbers
            print("\n5. Generating order numbers...")

            result = connection.execute(text("""
                SELECT id, created_at FROM orders WHERE order_number IS NULL
            """))

            orders_without_number = result.fetchall()

            for order in orders_without_number:
                order_id, created_at = order
                timestamp = created_at.strftime('%Y%m%d%H%M%S') if created_at else datetime.utcnow().strftime(
                    '%Y%m%d%H%M%S')
                random_num = random.randint(1000, 9999)
                order_number = f'ORD-{timestamp}-{random_num}'

                connection.execute(
                    text("UPDATE orders SET order_number = :order_number WHERE id = :id"),
                    {"order_number": order_number, "id": order_id}
                )

            print(f"   Generated order numbers for {len(orders_without_number)} orders")

            # 6. Calculate subtotals from order_items
            print("\n6. Calculating subtotals...")

            connection.execute(text("""
                UPDATE orders o
                SET subtotal = COALESCE((
                    SELECT SUM(total_price)
                    FROM order_items oi
                    WHERE oi.order_id = o.id
                ), total_amount)
                WHERE subtotal IS NULL
            """))

            # 7. Set defaults for other columns
            print("\n7. Setting default values...")

            connection.execute(text("UPDATE orders SET tax_amount = 0 WHERE tax_amount IS NULL"))
            connection.execute(text("UPDATE orders SET shipping_amount = 0 WHERE shipping_amount IS NULL"))

            # For orders with no shipping_address, set a default
            connection.execute(text("""
                UPDATE orders 
                SET shipping_address = '{"address": "Not specified"}'::JSONB
                WHERE shipping_address IS NULL OR shipping_address = ''
            """))

            # 8. Make columns NOT NULL
            print("\n8. Making columns NOT NULL...")

            # Try to make order_number NOT NULL
            try:
                # First check for nulls
                result = connection.execute(text("SELECT COUNT(*) FROM orders WHERE order_number IS NULL"))
                null_count = result.fetchone()[0]

                if null_count == 0:
                    connection.execute(text("ALTER TABLE orders ALTER COLUMN order_number SET NOT NULL"))
                    print("   Made order_number NOT NULL")
                else:
                    print(f"   WARNING: {null_count} orders still have null order_number")
            except Exception as e:
                print(f"   Could not make order_number NOT NULL: {e}")

            # Make numeric columns NOT NULL
            for column in ['subtotal', 'tax_amount', 'shipping_amount']:
                try:
                    connection.execute(text(f"UPDATE orders SET {column} = 0 WHERE {column} IS NULL"))
                    connection.execute(text(f"ALTER TABLE orders ALTER COLUMN {column} SET NOT NULL"))
                    print(f"   Made {column} NOT NULL")
                except Exception as e:
                    print(f"   Could not make {column} NOT NULL: {e}")

            # 9. Add unique constraint on order_number
            print("\n9. Adding unique constraint...")
            try:
                connection.execute(text("ALTER TABLE orders ADD CONSTRAINT uq_order_number UNIQUE (order_number)"))
                print("   Added unique constraint on order_number")
            except Exception as e:
                print(f"   Could not add unique constraint: {e}")

            # 10. Remove old columns from orders (product_id, quantity)
            print("\n10. Removing old columns from orders...")

            # Check if we can safely remove these columns
            result = connection.execute(text("""
                SELECT COUNT(*) FROM orders 
                WHERE product_id IS NOT NULL OR quantity IS NOT NULL
            """))
            count_with_data = result.fetchone()[0]

            if count_with_data == 0 or input(f"Remove product_id and quantity from orders? (y/n): ").lower() == 'y':
                for column in ['product_id', 'quantity']:
                    try:
                        # Check if column exists
                        result = connection.execute(text(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'orders' AND column_name = '{column}'
                        """))

                        if result.fetchone():
                            # Drop foreign key if it exists
                            if column == 'product_id':
                                try:
                                    connection.execute(
                                        text("ALTER TABLE orders DROP CONSTRAINT orders_product_id_fkey"))
                                except:
                                    pass

                            connection.execute(text(f"ALTER TABLE orders DROP COLUMN {column}"))
                            print(f"   Removed {column} from orders")
                    except Exception as e:
                        print(f"   Could not remove {column}: {e}")

            trans.commit()
            print("\n✅ Database schema fix completed!")

            return True

        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error fixing database: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            connection.close()


def verify_fix():
    with app.app_context():
        connection = db.engine.connect()

        try:
            print("\n=== Verifying Database ===")

            # Check orders table
            print("\n1. Orders table:")
            result = connection.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(order_number) as with_order_number,
                       COUNT(DISTINCT order_number) as unique_order_numbers
                FROM orders
            """))
            stats = result.fetchone()
            print(f"   Total orders: {stats[0]}")
            print(f"   With order_number: {stats[1]}")
            print(f"   Unique order numbers: {stats[2]}")

            # Sample orders
            print("\n2. Sample orders:")
            result = connection.execute(text("""
                SELECT o.id, o.order_number, o.status, o.subtotal, o.total_amount,
                       COUNT(oi.id) as item_count,
                       STRING_AGG(p.title, ', ') as products
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                LEFT JOIN products p ON oi.product_id = p.id
                GROUP BY o.id
                ORDER BY o.id DESC
                LIMIT 3
            """))

            for row in result.fetchall():
                print(f"   Order #{row[0]}: {row[1] or 'No number'}")
                print(f"     Status: {row[2]}, Subtotal: ${row[3] or 0:.2f}, Items: {row[5]}")
                if row[6]:
                    print(f"     Products: {row[6]}")

            # Check order_items
            print("\n3. Order items summary:")
            result = connection.execute(text("""
                SELECT COUNT(*) as total_items,
                       COUNT(DISTINCT order_id) as orders_with_items,
                       AVG(quantity) as avg_quantity,
                       SUM(total_price) as total_revenue
                FROM order_items
            """))
            items_stats = result.fetchone()
            print(f"   Total items: {items_stats[0]}")
            print(f"   Orders with items: {items_stats[1]}")
            print(f"   Average quantity: {items_stats[2]:.1f}")
            print(f"   Total revenue: ${items_stats[3] or 0:.2f}")

            print("\n✅ Verification complete!")

        except Exception as e:
            print(f"❌ Verification error: {e}")
        finally:
            connection.close()


def create_test_data():
    """Create test data if needed"""
    with app.app_context():
        connection = db.engine.connect()
        trans = connection.begin()

        try:
            print("\n=== Creating Test Data ===")

            # Check if we have users
            result = connection.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]

            if user_count == 0:
                print("Creating test user...")
                connection.execute(text("""
                    INSERT INTO users (email, name, password_hash, role, created_at)
                    VALUES ('test@example.com', 'Test User', 
                            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 
                            'customer', NOW())
                    RETURNING id
                """))
                user_id = connection.fetchone()[0]
                print(f"Created user with ID: {user_id}")
            else:
                result = connection.execute(text("SELECT id FROM users LIMIT 1"))
                user_id = result.fetchone()[0]

            # Check if we have products
            result = connection.execute(text("SELECT COUNT(*) FROM products"))
            product_count = result.fetchone()[0]

            if product_count == 0:
                print("Creating test products...")
                products = [
                    ('Classic T-Shirt', 'Comfortable cotton t-shirt', 24.99, 100),
                    ('Premium Polo', 'High-quality polo shirt', 39.99, 50),
                    ('Hoodie', 'Warm and cozy hoodie', 59.99, 30)
                ]

                for title, description, price, stock in products:
                    connection.execute(text("""
                        INSERT INTO products (title, description, price, stock_quantity, created_at)
                        VALUES (:title, :description, :price, :stock, NOW())
                    """), {
                        'title': title,
                        'description': description,
                        'price': price,
                        'stock': stock
                    })

                print("Created 3 test products")

            # Create a test order
            print("Creating test order...")
            order_number = f'TEST-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}'

            connection.execute(text("""
                INSERT INTO orders (user_id, order_number, status, total_amount, 
                                  subtotal, tax_amount, shipping_amount, 
                                  shipping_address, created_at)
                VALUES (:user_id, :order_number, 'pending', :total, 
                        :subtotal, :tax, :shipping, :address, NOW())
                RETURNING id
            """), {
                'user_id': user_id,
                'order_number': order_number,
                'total': 84.97,
                'subtotal': 64.98,
                'tax': 10.40,
                'shipping': 9.99,
                'address': json.dumps({
                    'street': '123 Test St',
                    'city': 'Nairobi',
                    'country': 'Kenya',
                    'postal_code': '00100'
                })
            })

            order_id = connection.fetchone()[0]

            # Add order items
            result = connection.execute(text("SELECT id, price, title FROM products LIMIT 2"))
            products = result.fetchall()

            for i, (product_id, price, title) in enumerate(products):
                quantity = i + 1
                connection.execute(text("""
                    INSERT INTO order_items 
                    (order_id, product_id, product_title, product_price, 
                     quantity, total_price, unit_price, created_at)
                    VALUES (:order_id, :product_id, :title, :price,
                            :quantity, :total, :price, NOW())
                """), {
                    'order_id': order_id,
                    'product_id': product_id,
                    'title': title,
                    'price': price,
                    'quantity': quantity,
                    'total': price * quantity
                })

            trans.commit()
            print(f"✅ Created test order #{order_id} with number {order_number}")

        except Exception as e:
            trans.rollback()
            print(f"❌ Error creating test data: {e}")
        finally:
            connection.close()


if __name__ == '__main__':
    print("Starting database fix...")

    if fix_database_schema():
        verify_fix()

        # Ask to create test data
        response = input("\nCreate test data? (y/n): ")
        if response.lower() == 'y':
            create_test_data()
            verify_fix()