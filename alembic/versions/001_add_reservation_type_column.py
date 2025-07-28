"""Add reservation_type column to reservations table

Revision ID: 001
Revises: 
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add reservation_type column to reservations table
    op.add_column('reservations', 
                  sa.Column('reservation_type', 
                           sa.Enum('dining', 'fun', 'team_event', 'birthday', 'party', 'special_event', 
                                   name='reservationtype'), 
                           server_default='dining', 
                           nullable=False))


def downgrade() -> None:
    # Remove reservation_type column
    op.drop_column('reservations', 'reservation_type')
    op.execute('DROP TYPE IF EXISTS reservationtype')