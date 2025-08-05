"""Create table_layouts table

Revision ID: 003
Revises: 002
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tableshape enum
    tableshape = postgresql.ENUM('rectangular', 'round', 'square', 'bar_stool', 'custom', name='tableshape')
    tableshape.create(op.get_bind())
    
    # Create table_layouts table
    op.create_table('table_layouts',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('table_id', sa.Text(), nullable=False),
        sa.Column('room_id', sa.Text(), nullable=False),
        sa.Column('x_position', sa.Float(), nullable=False),
        sa.Column('y_position', sa.Float(), nullable=False),
        sa.Column('width', sa.Float(), nullable=True, server_default='100.0'),
        sa.Column('height', sa.Float(), nullable=True, server_default='80.0'),
        sa.Column('shape', sa.Enum('rectangular', 'round', 'square', 'bar_stool', 'custom', name='tableshape'), nullable=False, server_default='rectangular'),
        sa.Column('color', sa.String(), nullable=True, server_default='#4A90E2'),
        sa.Column('border_color', sa.String(), nullable=True, server_default='#2E5BBA'),
        sa.Column('text_color', sa.String(), nullable=True, server_default='#FFFFFF'),
        sa.Column('show_capacity', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('show_name', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('font_size', sa.Integer(), nullable=True, server_default='12'),
        sa.Column('custom_capacity', sa.Integer(), nullable=True),
        sa.Column('is_connected', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('connected_to', sa.Text(), nullable=True),
        sa.Column('z_index', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['connected_to'], ['table_layouts.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.ForeignKeyConstraint(['table_id'], ['tables.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('table_id')
    )


def downgrade() -> None:
    # Drop table_layouts table
    op.drop_table('table_layouts')
    
    # Drop tableshape enum
    tableshape = postgresql.ENUM('rectangular', 'round', 'square', 'bar_stool', 'custom', name='tableshape')
    tableshape.drop(op.get_bind()) 