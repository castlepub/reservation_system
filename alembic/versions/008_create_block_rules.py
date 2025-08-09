"""create recurring block rules

Revision ID: 008_create_block_rules
Revises: 007_create_blocks
Create Date: 2025-08-09
"""

from alembic import op
import sqlalchemy as sa


revision = '008_create_block_rules'
down_revision = '007_create_blocks'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'room_block_rules',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('room_id', sa.Text(), sa.ForeignKey('rooms.id'), nullable=False),
        sa.Column('day_of_week', sa.Enum('monday','tuesday','wednesday','thursday','friday','saturday','sunday', name='dayofweek'), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('public_only', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'table_block_rules',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('table_id', sa.Text(), sa.ForeignKey('tables.id'), nullable=False),
        sa.Column('day_of_week', sa.Enum('monday','tuesday','wednesday','thursday','friday','saturday','sunday', name='dayofweek'), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('public_only', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('table_block_rules')
    op.drop_table('room_block_rules')


