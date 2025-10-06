from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.db.base import Base


print(">>> DEBUG: env.py loaded, running migrations mode:", "offline" if context.is_offline_mode() else "online")

# Import models here so that Base.metadata is populated
from app.models import (
    comment,
    comment_sentiment,
    keyword,
    membership,
    org,
    sentiment_aggregate,
    user,
    video,
)

# this is the Alembic Config object
config = context.config

# --- Determine DB URL ---
# Allow override via -x db_url=... (for tests), otherwise use settings
x_args = context.get_x_argument(as_dictionary=True)
if "db_url" in x_args:
    db_url = x_args["db_url"]
else:
    db_url = settings.DATABASE_URL

# ensure psycopg2 for Alembic
if db_url.startswith("postgresql+asyncpg"):
    db_url = db_url.replace("+asyncpg", "+psycopg2")

config.set_main_option("sqlalchemy.url", db_url)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

