"""add unlock_at to blocks

Revision ID: 009_add_unlock_at
Revises: 008_create_block_rules
Create Date: 2025-08-09
"""

from alembic import op
import sqlalchemy as sa


revision = '009_add_unlock_at'
down_revision = '008_create_block_rules'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('room_blocks', sa.Column('unlock_at', sa.DateTime(), nullable=True))
    op.add_column('table_blocks', sa.Column('unlock_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('table_blocks', 'unlock_at')
    op.drop_column('room_blocks', 'unlock_at')


