# add_profile_columns.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def add_profile_columns():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return

    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        print("=== Adding profile columns to users table ===")

        # Add each column individually
        columns_to_add = [
            ('bio', 'TEXT'),
            ('location', 'VARCHAR(200)'),
            ('website', 'VARCHAR(500)'),
            ('phone', 'VARCHAR(20)'),
            ('avatar_url', 'VARCHAR(500)'),
            ('banner_url', 'VARCHAR(500)')
        ]

        for column_name, column_type in columns_to_add:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
            except Exception as e:
                print(f"⚠️  Could not add {column_name}: {e}")

        conn.commit()
        print("✅ All columns added successfully!")

        # Verify the columns were added
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('bio', 'location', 'website', 'phone', 'avatar_url', 'banner_url')
        """)
        added_columns = cur.fetchall()
        print(f"Verified columns: {added_columns}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    add_profile_columns()