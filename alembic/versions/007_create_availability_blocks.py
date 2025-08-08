from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_create_availability_blocks'
down_revision = '006_add_public_bookable_to_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'availability_blocks',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('scope', sa.Enum('global', 'room', 'table', name='blockscope'), nullable=False),
        sa.Column('target_id', sa.Text(), nullable=True),
        sa.Column('block_type', sa.Enum('blackout', 'release', name='blocktype'), nullable=False),
        sa.Column('start_datetime', sa.DateTime(), nullable=True),
        sa.Column('end_datetime', sa.DateTime(), nullable=True),
        sa.Column('recurrence', sa.Enum('none', 'weekly', name='recurrence'), nullable=False, server_default='none'),
        sa.Column('weekdays', sa.Text(), nullable=True),
        sa.Column('release_time', sa.Time(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=False, server_default='Europe/Berlin'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('availability_blocks')
    op.execute("DROP TYPE IF EXISTS blockscope")
    op.execute("DROP TYPE IF EXISTS blocktype")
    op.execute("DROP TYPE IF EXISTS recurrence")


