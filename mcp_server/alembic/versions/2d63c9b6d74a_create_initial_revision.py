"""Create initial revision

Revision ID: 2d63c9b6d74a
Revises: 
Create Date: 2025-05-21 19:28:42.945280

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '2d63c9b6d74a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create oauth_clients table
    op.create_table('oauth_clients',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('client_id', sa.UUID(), nullable=False, unique=True, index=True),
        sa.Column('client_secret', sa.String(), nullable=False),
        sa.Column('client_name', sa.String(), nullable=False),
        sa.Column('redirect_uris', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('scopes', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('is_confidential', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create memories table with pgvector
    op.create_table('memories',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('encrypted_text', sa.Text(), nullable=True),
        sa.Column('permission', sa.String(), nullable=False, default='private'),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('expiration_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create authorization_codes table
    op.create_table('authorization_codes',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('code', sa.String(), nullable=False, index=True),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('redirect_uri', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), nullable=False),
        sa.Column('expires_at', sa.String(), nullable=False),
        sa.Column('code_challenge', sa.String(), nullable=True),
        sa.Column('code_challenge_method', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tokens table
    op.create_table('tokens',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('access_token', sa.String(), nullable=False, index=True),
        sa.Column('refresh_token', sa.String(), nullable=False, index=True),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('scope', sa.String(), nullable=False),
        sa.Column('access_token_expires_at', sa.String(), nullable=False),
        sa.Column('refresh_token_expires_at', sa.String(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('tokens')
    op.drop_table('authorization_codes')
    op.drop_table('memories')
    op.drop_table('oauth_clients')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS vector')
