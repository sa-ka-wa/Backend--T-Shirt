"""Add slug and contact_email to brands

Revision ID: d075eebcd14a
Revises: 9e83ff457874
Create Date: 2025-12-29 11:42:49.439819
"""
from alembic import op
import sqlalchemy as sa
import re


# revision identifiers, used by Alembic.
revision = 'd075eebcd14a'
down_revision = '9e83ff457874'
branch_labels = None
depends_on = None


def generate_slug(name):
    """Generate slug from brand name"""
    if not name:
        return 'brand'
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces and multiple hyphens
    return slug[:100]  # Truncate to max length


def upgrade():
    # Step 1: Add slug as nullable and contact_email
    with op.batch_alter_table('brands', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('contact_email', sa.String(length=100), nullable=True))

    connection = op.get_bind()

    # Step 2: Populate slugs for existing brands
    brands = connection.execute(sa.text("SELECT id, name FROM brands")).fetchall()
    existing_slugs = set(
        row[0] for row in connection.execute(sa.text("SELECT slug FROM brands WHERE slug IS NOT NULL"))
    )

    for brand_id, brand_name in brands:
        slug = generate_slug(brand_name)
        original_slug = slug
        counter = 1

        while slug in existing_slugs:
            slug = f"{original_slug}-{counter}"
            counter += 1

        existing_slugs.add(slug)
        connection.execute(sa.text("UPDATE brands SET slug = :slug WHERE id = :id"), {'slug': slug, 'id': brand_id})

    # Step 3: Make slug NOT NULL and unique
    with op.batch_alter_table('brands', schema=None) as batch_op:
        batch_op.alter_column('slug', existing_type=sa.String(length=100), nullable=False)
        batch_op.create_unique_constraint('uq_brands_slug', ['slug'])


def downgrade():
    with op.batch_alter_table('brands', schema=None) as batch_op:
        batch_op.drop_column('contact_email')
        batch_op.drop_constraint('uq_brands_slug', type_='unique')
        batch_op.drop_column('slug')
