"""add public_bookable to tables

Revision ID: 006_add_public_bookable
Revises: 005_add_area_management
Create Date: 2025-08-08
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_public_bookable_to_tables'
down_revision = '005_add_area_management'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tables', sa.Column('public_bookable', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column('tables', 'public_bookable')


