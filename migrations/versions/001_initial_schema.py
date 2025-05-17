"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-05-16 17:10:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Create oauth_clients table with string client_id
    op.create_table('oauth_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('client_secret', sa.String(), nullable=False),
        sa.Column('redirect_uris', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('allowed_scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    
    # Create oauth_tokens table with string client_id and PKCE support
    op.create_table('oauth_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('token_type', sa.String(), nullable=False, default='bearer'),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('code_challenge', sa.String(), nullable=True),
        sa.Column('code_challenge_method', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('access_token'),
        sa.UniqueConstraint('refresh_token'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.client_id'])
    )
    
    # Create memories table
    op.create_table('memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )


def downgrade() -> None:
    op.drop_table('memories')
    op.drop_table('oauth_tokens')
    op.drop_table('oauth_clients')
    op.drop_table('users')
