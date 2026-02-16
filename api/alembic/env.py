from logging.config import fileConfig
import logging

from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
logger = logging.getLogger(__name__)


def _ensure_alembic_version_column_length(connection) -> None:
    # Some local revision IDs are longer than 32 chars (for example merge revisions).
    # If the project was bootstrapped with varchar(32), alembic crashes while inserting
    # the revision into alembic_version. Widen the column before running migrations.
    try:
        table_exists = connection.execute(text("SELECT to_regclass('public.alembic_version') IS NOT NULL")).scalar_one()
    except ProgrammingError:
        logger.exception("Failed to check alembic_version existence")
        raise

    if not table_exists:
        logger.info("alembic_version table not found, skip pre-migration fix")
        return

    column_info = connection.execute(
        text(
            """
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'alembic_version'
              AND column_name = 'version_num'
            """
        )
    ).first()

    if (
        column_info
        and column_info.data_type == "character varying"
        and column_info.character_maximum_length is not None
        and column_info.character_maximum_length == 32
    ):
        connection.execute(
            text(
                """
                ALTER TABLE alembic_version
                ALTER COLUMN version_num TYPE VARCHAR(64)
                """
            )
        )
        logger.info("alembic_version.version_num widened to varchar(64)")
    else:
        logger.info("alembic_version.version_num ok")


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            _ensure_alembic_version_column_length(connection)
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
