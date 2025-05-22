"""
Create token blacklist table for token revocation.

Revision ID: token_blacklist_migration
Revises: 
Create Date: 2025-05-22 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'token_blacklist_migration'
down_revision = '2d63c9b6d74a'  # Updated to chain with the existing head revision
branch_labels = None
depends_on = None


def upgrade():
    # Check if the table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'token_blacklist' not in inspector.get_table_names():
        # Create token_blacklist table
        op.create_table(
            'token_blacklist',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('token_jti', sa.String(), nullable=False),
            sa.Column('blacklisted_at', sa.DateTime(), nullable=False),
            sa.Column('reason', sa.String(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        
        # Create index on token_jti for faster lookups
        op.create_index(op.f('ix_token_blacklist_token_jti'), 'token_blacklist', ['token_jti'], unique=False)


def downgrade():
    # Check if the table exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'token_blacklist' in inspector.get_table_names():
        # Drop index
        op.drop_index(op.f('ix_token_blacklist_token_jti'), table_name='token_blacklist')
        
        # Drop token_blacklist table
        op.drop_table('token_blacklist')
