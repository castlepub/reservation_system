"""Add duration_hours column to reservations table

Revision ID: 002
Revises: 001
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add duration_hours column to reservations table
    op.add_column('reservations', 
                  sa.Column('duration_hours', 
                           sa.Integer(), 
                           server_default='2', 
                           nullable=False))


def downgrade() -> None:
    # Remove duration_hours column
    op.drop_column('reservations', 'duration_hours') 