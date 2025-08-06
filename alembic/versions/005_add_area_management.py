"""Add area management fields to rooms table

Revision ID: 005
Revises: 004
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create areatype enum
    areatype = postgresql.ENUM('indoor', 'outdoor', 'shared', name='areatype')
    areatype.create(op.get_bind())
    
    # Add area management columns to rooms table
    op.add_column('rooms', sa.Column('area_type', sa.Enum('indoor', 'outdoor', 'shared', name='areatype'), nullable=False, server_default='indoor'))
    op.add_column('rooms', sa.Column('priority', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('rooms', sa.Column('is_fallback_area', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('rooms', sa.Column('fallback_for', sa.Text(), nullable=True))
    op.add_column('rooms', sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove area management columns
    op.drop_column('rooms', 'display_order')
    op.drop_column('rooms', 'fallback_for')
    op.drop_column('rooms', 'is_fallback_area')
    op.drop_column('rooms', 'priority')
    op.drop_column('rooms', 'area_type')
    
    # Drop areatype enum
    areatype = postgresql.ENUM('indoor', 'outdoor', 'shared', name='areatype')
    areatype.drop(op.get_bind()) 