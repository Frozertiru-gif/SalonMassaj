from logging.config import fileConfig
import logging

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
logger = logging.getLogger(__name__)


ALEMBIC_VERSION_TABLE = "alembic_version"
ALEMBIC_VERSION_COLUMN_LENGTH = 255


def _quote_ident(connection, ident: str) -> str:
    return connection.dialect.identifier_preparer.quote(ident)


def _format_qualified_name(connection, schema: str | None, table: str) -> str:
    quoted_table = _quote_ident(connection, table)
    if not schema:
        return quoted_table
    return f"{_quote_ident(connection, schema)}.{quoted_table}"


def ensure_alembic_version_table(connection, schema: str | None, size: int = ALEMBIC_VERSION_COLUMN_LENGTH) -> None:
    # Some local revision IDs are longer than 32 chars.
    # Keep alembic_version.version_num wide enough before migrations run.
    table_schema = schema or connection.exec_driver_sql("SELECT current_schema()").scalar_one()
    qualified_table = _format_qualified_name(connection, table_schema, ALEMBIC_VERSION_TABLE)

    table_exists = connection.exec_driver_sql(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %(table_schema)s
              AND table_name = %(table_name)s
        )
        """,
        {"table_schema": table_schema, "table_name": ALEMBIC_VERSION_TABLE},
    ).scalar_one()

    if not table_exists:
        connection.exec_driver_sql(
            f"""
            CREATE TABLE {qualified_table} (
                version_num VARCHAR({size}) NOT NULL,
                CONSTRAINT {ALEMBIC_VERSION_TABLE}_pkc PRIMARY KEY (version_num)
            )
            """
        )
        logger.info("Ensured %s in schema=%s with version_num_length=%s", qualified_table, table_schema, size)
        return

    column_info = connection.exec_driver_sql(
        """
        SELECT data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = %(table_schema)s
          AND table_name = %(table_name)s
          AND column_name = 'version_num'
        """,
        {"table_schema": table_schema, "table_name": ALEMBIC_VERSION_TABLE},
    ).first()

    if column_info is None:
        connection.exec_driver_sql(
            f"ALTER TABLE {qualified_table} ADD COLUMN version_num VARCHAR({size})"
        )

        has_primary_key = connection.exec_driver_sql(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE table_schema = %(table_schema)s
                  AND table_name = %(table_name)s
                  AND constraint_type = 'PRIMARY KEY'
            )
            """,
            {"table_schema": table_schema, "table_name": ALEMBIC_VERSION_TABLE},
        ).scalar_one()

        if not has_primary_key:
            connection.exec_driver_sql(
                f"ALTER TABLE {qualified_table} ADD CONSTRAINT {ALEMBIC_VERSION_TABLE}_pkc PRIMARY KEY (version_num)"
            )
        logger.info("Added missing %s.version_num column", qualified_table)
        return

    current_length = column_info.character_maximum_length if column_info is not None else None

    needs_widening = (
        column_info
        and column_info.data_type in {"character varying", "character"}
        and current_length is not None
        and current_length < size
    )

    if needs_widening:
        connection.exec_driver_sql(
            f"""
            ALTER TABLE {qualified_table}
            ALTER COLUMN version_num TYPE VARCHAR({size})
            """
        )
        current_length = size

    logger.info(
        "Checked %s (schema=%s), version_num_length=%s",
        qualified_table,
        table_schema,
        current_length,
    )


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
        version_table_schema = config.get_main_option("version_table_schema") or None
        context_configure_kwargs = {
            "connection": connection,
            "target_metadata": target_metadata,
        }
        if version_table_schema:
            context_configure_kwargs["version_table_schema"] = version_table_schema

        try:
            ensure_alembic_version_table(connection, version_table_schema)
        except ProgrammingError:
            logger.exception("Failed to ensure alembic version table")
            raise

        context.configure(**context_configure_kwargs)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
