# fix_brand_ids_simple.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def fix_brand_ids():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return

    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        print("=== Fixing NULL brand_id values ===")

        # Check for users with NULL brand_id
        cur.execute("SELECT COUNT(*) FROM users WHERE brand_id IS NULL")
        null_count = cur.fetchone()[0]
        print(f"Found {null_count} users with NULL brand_id")

        if null_count > 0:
            # Get or create a default brand
            cur.execute("SELECT id FROM brands LIMIT 1")
            brand = cur.fetchone()

            if not brand:
                print("No brands found, creating a default brand...")
                cur.execute("""
                    INSERT INTO brands (name, subdomain) 
                    VALUES ('Default Brand', 'default') 
                    RETURNING id
                """)
                brand = cur.fetchone()
                print(f"Created default brand with ID: {brand[0]}")
            else:
                print(f"Using existing brand with ID: {brand[0]}")

            # Update users with NULL brand_id
            cur.execute(f"UPDATE users SET brand_id = {brand[0]} WHERE brand_id IS NULL")
            print(f"Updated {null_count} users to brand_id {brand[0]}")

            # Commit changes
            conn.commit()
            print("✅ All users updated successfully!")
        else:
            print("✅ No users with NULL brand_id found!")

        # Verify the fix
        cur.execute("SELECT COUNT(*) FROM users WHERE brand_id IS NULL")
        remaining_null = cur.fetchone()[0]
        print(f"Remaining users with NULL brand_id: {remaining_null}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    fix_brand_ids()