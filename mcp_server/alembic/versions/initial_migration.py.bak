"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-05-20 18:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Create oauth_clients table
    op.create_table('oauth_clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', sa.String(), nullable=False, unique=True),
        sa.Column('client_secret', sa.String(), nullable=False),
        sa.Column('client_name', sa.String(), nullable=False),
        sa.Column('redirect_uris', sa.String(), nullable=False),
        sa.Column('grant_types', sa.String(), nullable=False),
        sa.Column('response_types', sa.String(), nullable=False),
        sa.Column('scopes', sa.String(), nullable=False),
        sa.Column('client_uri', sa.String(), nullable=True),
        sa.Column('logo_uri', sa.String(), nullable=True),
        sa.Column('tos_uri', sa.String(), nullable=True),
        sa.Column('policy_uri', sa.String(), nullable=True),
        sa.Column('jwks_uri', sa.String(), nullable=True),
        sa.Column('software_id', sa.String(), nullable=True),
        sa.Column('software_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    
    # Create memories table
    op.create_table('memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('encrypted_text', sa.Text(), nullable=True),
        sa.Column('permission', sa.String(), nullable=False, default='private'),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('expiration_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create oauth_tokens table
    op.create_table('oauth_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('access_token', sa.String(), nullable=False, unique=True),
        sa.Column('refresh_token', sa.String(), nullable=False, unique=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scopes', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('access_token'),
        sa.UniqueConstraint('refresh_token')
    )
    
    # Create indexes
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_oauth_clients_client_id'), 'oauth_clients', ['client_id'], unique=True)
    op.create_index(op.f('ix_memories_user_id'), 'memories', ['user_id'], unique=False)
    op.create_index(op.f('ix_oauth_tokens_access_token'), 'oauth_tokens', ['access_token'], unique=True)
    op.create_index(op.f('ix_oauth_tokens_refresh_token'), 'oauth_tokens', ['refresh_token'], unique=True)


def downgrade():
    # Drop tables
    op.drop_table('oauth_tokens')
    op.drop_table('memories')
    op.drop_table('oauth_clients')
    op.drop_table('users')
    
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
