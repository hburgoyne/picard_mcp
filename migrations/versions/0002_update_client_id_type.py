from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_update_client_id_type'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, create a temporary column to store the new string client_id
    op.add_column('oauth_tokens', sa.Column('temp_client_id', sa.String(), nullable=True))
    
    # Update the temporary column with the string version of client_id
    op.execute("""
        UPDATE oauth_tokens
        SET temp_client_id = (
            SELECT client_id
            FROM oauth_clients
            WHERE oauth_tokens.client_id = oauth_clients.id
        )
    """)
    
    # Drop the old client_id column and rename the temporary column
    op.drop_column('oauth_tokens', 'client_id')
    op.alter_column('oauth_tokens', 'temp_client_id', new_column_name='client_id', nullable=False)
    
    # Update the foreign key constraint
    op.create_foreign_key(
        'fk_oauth_tokens_client_id_oauth_clients',
        'oauth_tokens',
        'oauth_clients',
        ['client_id'],
        ['client_id']
    )

def downgrade() -> None:
    # First, create a temporary column to store the old integer client_id
    op.add_column('oauth_tokens', sa.Column('temp_client_id', sa.Integer(), nullable=True))
    
    # Update the temporary column with the integer version of client_id
    op.execute("""
        UPDATE oauth_tokens
        SET temp_client_id = (
            SELECT id
            FROM oauth_clients
            WHERE oauth_tokens.client_id = oauth_clients.client_id
        )
    """)
    
    # Drop the old client_id column and rename the temporary column
    op.drop_column('oauth_tokens', 'client_id')
    op.alter_column('oauth_tokens', 'temp_client_id', new_column_name='client_id', nullable=False)
    
    # Update the foreign key constraint
    op.create_foreign_key(
        'fk_oauth_tokens_client_id_oauth_clients',
        'oauth_tokens',
        'oauth_clients',
        ['client_id'],
        ['id']
    )
