"""Create room_layouts table

Revision ID: 004
Revises: 003
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create room_layouts table
    op.create_table('room_layouts',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('room_id', sa.Text(), nullable=False),
        sa.Column('width', sa.Float(), nullable=True, server_default='800.0'),
        sa.Column('height', sa.Float(), nullable=True, server_default='600.0'),
        sa.Column('background_color', sa.String(), nullable=True, server_default='#F5F5F5'),
        sa.Column('grid_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('grid_size', sa.Integer(), nullable=True, server_default='20'),
        sa.Column('grid_color', sa.String(), nullable=True, server_default='#E0E0E0'),
        sa.Column('show_entrance', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('entrance_position', sa.String(), nullable=True, server_default='top'),
        sa.Column('show_bar', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('bar_position', sa.String(), nullable=True, server_default='center'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id')
    )


def downgrade() -> None:
    # Drop room_layouts table
    op.drop_table('room_layouts') 