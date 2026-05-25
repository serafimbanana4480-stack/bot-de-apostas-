import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Append current directory to path so we can resolve src module
sys.path.append(os.getcwd())

# Import the database Base and models for autogenerate metadata discovery
from src.database.connection import Base
# Importing models registers them to the Base metadata
from src.database.models import RawGame, CleanGame, FeatureRow, CircuitBreakerLog
from src.core.config import settings

# this is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    """
    Control which database objects Alembic tracks.
    This limits migrations to our custom schemas and avoids scanning public schemas.
    """
    if type_ == "table":
        # Check if the table schema is in our defined schemas
        schema = object.schema
        return schema in ["bronze", "silver", "gold", "meta"]
    return True

def get_url():
    """Retrieve database URL from settings dynamically."""
    return (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Override connection URL with setting values
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
