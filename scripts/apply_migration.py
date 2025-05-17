from alembic.config import Config
from alembic import command

# Set up the alembic configuration
alembic_cfg = Config()
alembic_cfg.set_main_option('script_location', 'migrations')
alembic_cfg.set_main_option('sqlalchemy.url', 'postgresql://postgres:postgres@db:5433/picard_mcp')

# Apply the migration
command.upgrade(alembic_cfg, 'head')
print("Migration applied successfully!")
