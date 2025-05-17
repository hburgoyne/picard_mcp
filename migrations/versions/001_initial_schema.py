"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-05-15

"""
from alembic import op
import sqlalchemy as sa
import pgvector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create oauth_clients table
    op.create_table('oauth_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('client_secret', sa.String(), nullable=False),
        sa.Column('redirect_uris', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('allowed_scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_clients_client_id'), 'oauth_clients', ['client_id'], unique=True)
    op.create_index(op.f('ix_oauth_clients_id'), 'oauth_clients', ['id'], unique=False)
    
    # Create memories table
    op.create_table('memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column('permission', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memories_id'), 'memories', ['id'], unique=False)
    
    # Create oauth_tokens table
    op.create_table('oauth_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('token_type', sa.String(), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_tokens_access_token'), 'oauth_tokens', ['access_token'], unique=True)
    op.create_index(op.f('ix_oauth_tokens_id'), 'oauth_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_oauth_tokens_refresh_token'), 'oauth_tokens', ['refresh_token'], unique=True)
    
    # Create index for vector similarity search
    op.execute(
        'CREATE INDEX memories_embedding_idx ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_oauth_tokens_refresh_token'), table_name='oauth_tokens')
    op.drop_index(op.f('ix_oauth_tokens_id'), table_name='oauth_tokens')
    op.drop_index(op.f('ix_oauth_tokens_access_token'), table_name='oauth_tokens')
    op.drop_table('oauth_tokens')
    
    op.drop_index(op.f('ix_memories_id'), table_name='memories')
    op.drop_table('memories')
    
    op.drop_index(op.f('ix_oauth_clients_id'), table_name='oauth_clients')
    op.drop_index(op.f('ix_oauth_clients_client_id'), table_name='oauth_clients')
    op.drop_table('oauth_clients')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
