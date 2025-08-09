"""create room_blocks and table_blocks

Revision ID: 007_create_blocks
Revises: 006_add_public_bookable
Create Date: 2025-08-09
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_create_blocks'
down_revision = '006_add_public_bookable'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'room_blocks',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('room_id', sa.Text(), sa.ForeignKey('rooms.id'), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('public_only', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'table_blocks',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('table_id', sa.Text(), sa.ForeignKey('tables.id'), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('public_only', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('table_blocks')
    op.drop_table('room_blocks')


